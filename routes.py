import os
import json
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

from openai import OpenAI

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

        # Function to retrieve message details
        def retrieve_message(thread_id, message_id):
            try:
                message = client.beta.threads.messages.retrieve(
                    thread_id=thread_id,
                    message_id=message_id
                )
                # Serialize the message content properly
                def serialize_content(content):
                    if content.type == "text":
                        return {
                            "type": content.type,
                            "text": {
                                "value": content.text.value,
                                "annotations": content.text.annotations
                            }
                        }
                    elif content.type == "image_file":
                        return {
                            "type": content.type,
                            "image_file": {
                                "file_id": content.image_file.file_id,
                                "detail": content.image_file.detail
                            }
                        }
                    elif content.type == "image_url":
                        return {
                            "type": content.type,
                            "image_url": {
                                "url": content.image_url.url,
                                "detail": content.image_url.detail
                            }
                        }
                    return content

                return {
                    "id": message.id,
                    "object": message.object,
                    "created_at": message.created_at,
                    "thread_id": message.thread_id,
                    "status": message.status,
                    "incomplete_details": message.incomplete_details,
                    "completed_at": message.completed_at,
                    "incomplete_at": message.incomplete_at,
                    "role": message.role,
                    "content": [serialize_content(c) for c in message.content],
                    "assistant_id": message.assistant_id,
                    "run_id": message.run_id,
                    "attachments": message.attachments,
                    "metadata": message.metadata
                }
            except Exception as e:
                return {"error": str(e)}

        # Convert run_steps to a JSON serializable format
        def serialize_run_step(step):
            step_dict = {
                "id": step.id,
                "object": step.object,
                "created_at": step.created_at,
                "run_id": step.run_id,
                "assistant_id": step.assistant_id,
                "thread_id": step.thread_id,
                "type": step.type,
                "status": step.status,
                "cancelled_at": step.cancelled_at,
                "completed_at": step.completed_at,
                "expired_at": step.expired_at,
                "failed_at": step.failed_at,
                "last_error": None if step.last_error is None else {
                    "code": step.last_error.code,
                    "message": step.last_error.message,
                    "expired_at": step.last_error.expired_at,
                    "cancelled_at": step.last_error.cancelled_at,
                    "failed_at": step.last_error.failed_at
                },
                "metadata": step.metadata,
                "usage": None if step.usage is None else {
                    "prompt_tokens": step.usage.prompt_tokens,
                    "completion_tokens": step.usage.completion_tokens,
                    "total_tokens": step.usage.total_tokens
                }
            }
            
            # Add step details based on the type
            if step.type == "message_creation":
                message_id = step.step_details.message_creation.message_id
                message_details = retrieve_message(step.thread_id, message_id)
                step_dict["step_details"] = {
                    "type": step.step_details.type,
                    "message_creation": message_details
                }
            elif step.type == "tool_calls":
                tool_calls = []
                for tool_call in step.step_details.tool_calls:
                    tool_call_dict = {
                        "id": tool_call.id,
                        "type": tool_call.type
                    }
                    if tool_call.type == "code_interpreter":
                        tool_call_dict["code_interpreter"] = {
                            "input": tool_call.code_interpreter.input,
                            "outputs": [
                                {"type": output.type, "logs": output.logs} if output.type == "logs" else
                                {"type": output.type, "file_id": output.image.file_id}
                                for output in tool_call.code_interpreter.outputs
                            ]
                        }
                    elif tool_call.type == "file_search":
                        tool_call_dict["file_search"] = {}
                    elif tool_call.type == "function":
                        tool_call_dict["function"] = {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                            "output": tool_call.function.output,
                            "last_error": None if tool_call.function.last_error is None else {
                                "code": tool_call.function.last_error.code,
                                "message": tool_call.function.last_error.message
                            }
                        }
                    tool_calls.append(tool_call_dict)
                step_dict["step_details"] = {
                    "type": step.step_details.type,
                    "tool_calls": tool_calls
                }
            
            return step_dict

        serialized_run_steps = [serialize_run_step(step) for step in run_steps]

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
        content_type = "application/octet-stream"

        if file_info.filename.endswith('.json'):
            content_type = 'application/json'
        elif file_info.filename.endswith('.pdf'):
            content_type = 'application/pdf'
        elif file_info.filename.endswith('.png'):
            content_type = 'image/png'
        elif file_info.filename.endswith('.jpg') or file_info.filename.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif file_info.filename.endswith('.gif'):
            content_type = 'image/gif'
        elif file_info.filename.endswith('.bmp'):
            content_type = 'image/bmp'
        elif file_info.filename.endswith('.tiff') or file_info.filename.endswith('.tif'):
            content_type = 'image/tiff'
        elif file_info.filename.endswith('.webp'):
            content_type = 'image/webp'
        elif file_info.filename.endswith('.csv'):
            content_type = 'text/csv'

        file_data = client.files.with_raw_response.retrieve_content(file_id).content

        return file_data, 200, {"Content-Type": content_type}
    except Exception as e:
        return jsonify({"error": str(e)}), 500