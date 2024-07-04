import os
import json
import io
from PIL import Image
from flask import Blueprint, jsonify, request, send_file
from openai import OpenAI

from utils.serializers import serialize_run_step
from utils.file_utils import determine_content_type
from config.logging import setup_logger

logger = setup_logger()
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
api = Blueprint('api', __name__, url_prefix='/api')

# File to store threads
THREADS_FILE = "threads.json"
if not os.path.exists(THREADS_FILE):
    with open(THREADS_FILE, 'w') as f:
        json.dump({}, f, indent=4)

def write_to_json(thread_id, data):
    with open(THREADS_FILE, 'r') as f:
        file_data = json.load(f)

    if thread_id not in file_data:
        file_data[thread_id] = []

    file_data[thread_id].append(data)

    with open(THREADS_FILE, 'w') as f:
        json.dump(file_data, f, indent=4)

def update_run_steps(thread_id, run_id, serialized_run_steps, status):
    with open(THREADS_FILE, 'r') as f:
        file_data = json.load(f)

    if thread_id in file_data:
        for entry in file_data[thread_id]:
            if entry["server"]["run_id"] == run_id:
                if status == "completed":
                    # Reverse the run_steps
                    serialized_run_steps.reverse()

                    # Remove duplicates by file_id, keeping the latest
                    seen_file_ids = set()
                    unique_steps = []
                    for step in serialized_run_steps:
                        new_steps = []
                        for s in step["steps"]:
                            if s["type"] == "image":
                                if s["content"] not in seen_file_ids:
                                    new_steps.append(s)
                                    seen_file_ids.add(s["content"])
                            else:
                                new_steps.append(s)
                        if new_steps:
                            step["steps"] = new_steps
                            unique_steps.append(step)

                    entry["server"]["run_steps"] = unique_steps
                    entry["server"]["status"] = status
                else:
                    entry["server"]["run_steps"] = []
                    entry["server"]["status"] = "in_progress"
                break

    with open(THREADS_FILE, 'w') as f:
        json.dump(file_data, f, indent=4)

@api.route('/', methods=['GET'])
def health_check():
    try:
        logger.info("Health check endpoint hit")
        return jsonify({"status": "Ok"}), 200
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Create Thread
@api.route('/create-thread', methods=['POST'])
def create_thread():
    try:
        thread = client.beta.threads.create()
        logger.info(f"Created thread with ID: {thread.id}")
        return jsonify({"thread_id": thread.id}), 200
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add Message to Thread and Run
@api.route('/add-message', methods=['POST'])
def add_message():
    try:
        message = request.json.get('message')
        thread_id = request.json.get('thread_id')
        assistant_id = request.json.get('assistant_id')

        logger.info(f"Adding message to thread: {thread_id}, message: {message}")

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        logger.info(f"Created run with ID: {run.id}")

        # Log the client message to JSON file
        data = {
            "client": {
                "message": message
            },
            "server": {
                "run_steps": [],
                "status": "in_progress",
                "run_id": run.id
            }
        }
        write_to_json(thread_id, data)

        return jsonify({"run_id": run.id}), 200
    except Exception as e:
        logger.error(f"Error adding message: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get Run
@api.route('/get-run', methods=['POST'])
def get_run():
    try:
        thread_id = request.json.get('thread_id')
        run_id = request.json.get('run_id')

        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        status = run.status

        run_steps_result = client.beta.threads.runs.steps.list(
            thread_id=thread_id,
            run_id=run_id
        )
        run_steps = run_steps_result.data

        serialized_run_steps = [serialize_run_step(client, step) for step in run_steps]

        logger.info(f"Retrieved and serialized run: {run_id} for thread: {thread_id}")

        # Update the JSON file with the run steps only if status is completed
        if status == "completed":
            update_run_steps(thread_id, run_id, serialized_run_steps, status)

        # Prepare the response
        server_response = {
            "run_steps": serialized_run_steps if status == "completed" else [],
            "status": status,
            "run_id": run_id
        }

        return jsonify(server_response), 200
    except Exception as e:
        logger.error(f"Error retrieving run: {str(e)}")
        return jsonify({"error": str(e)}), 500

# FILES - GET FILE
@api.route('/get-file', methods=['POST'])
def get_file():
    try:
        file_id = request.json.get('file_id')
        if not file_id:
            logger.warning("file_id is required but not provided")
            return jsonify({"error": "file_id is required"}), 400

        file_info = client.files.retrieve(file_id)
        content_type = determine_content_type(file_info.filename)

        file_data = client.files.with_raw_response.retrieve_content(file_id).content

        if content_type != 'application/octet-stream':
            logger.warning(f"File {file_id} is not an octet-stream, it is {content_type}")
            return jsonify({"error": "File is not an octet-stream"}), 400

        # Convert the octet-stream to a PNG image
        image = Image.open(io.BytesIO(file_data))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        logger.info(f"Retrieved and converted file with ID: {file_id}")

        return send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"{file_info.filename}.png"
        )
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        return jsonify({"error": str(e)}), 500
