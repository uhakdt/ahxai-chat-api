import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

from openai import OpenAI
from utils import serialize_run_step
from file_utils import determine_content_type

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

@app.route('/', methods=['GET'])
def _():
    try:
        return jsonify({"status": "Ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create Thread
@app.route('/create-thread', methods=['POST'])
def create_thread():
    try:
        thread = client.beta.threads.create()
        return jsonify({"thread_id": thread.id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add Message to Thread and Run
@app.route('/add-message', methods=['POST'])
def add_message():
    try:
        message = request.json.get('message')
        thread_id = request.json.get('thread_id')
        assistant_id = request.json.get('assistant_id')

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        return jsonify({"run_id": run.id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Run
@app.route('/get-run', methods=['GET'])
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

        return jsonify({"status": status, "run_steps": serialized_run_steps}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# FILES - GET FILE
@app.route('/get-file', methods=['POST'])
def get_file():
    try:
        file_id = request.json.get('file_id')
        if not file_id:
            return jsonify({"error": "file_id is required"}), 400

        file_info = client.files.retrieve(file_id)
        content_type = determine_content_type(file_info.filename)

        file_data = client.files.with_raw_response.retrieve_content(file_id).content

        return file_data, 200, {"Content-Type": content_type}
    except Exception as e:
        return jsonify({"error": str(e)}), 500