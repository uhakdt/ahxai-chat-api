import io
from PIL import Image
from flask import send_file

from utils.serializers import serialize_run_step
from utils.json_utils import write_to_json, update_run_steps
from utils.file_utils import determine_content_type

def create_thread(client):
    thread = client.beta.threads.create()
    return thread.id

def add_message_to_thread(client, thread_id, message, assistant_id):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

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

    return run.id

def retrieve_run(client, thread_id, run_id):
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

    if status == "completed":
        update_run_steps(thread_id, run_id, serialized_run_steps, status)

    server_response = {
        "run_steps": serialized_run_steps if status == "completed" else [],
        "status": status,
        "run_id": run_id
    }

    return server_response

def get_file_data(client, file_id):
    file_info = client.files.retrieve(file_id)
    content_type = determine_content_type(file_info.filename)

    file_data = client.files.with_raw_response.retrieve_content(file_id).content

    if content_type != 'application/octet-stream':
        raise ValueError(f"File {file_id} is not an octet-stream, it is {content_type}")

    image = Image.open(io.BytesIO(file_data))
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return send_file(
        img_byte_arr,
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{file_info.filename}.png"
    )
