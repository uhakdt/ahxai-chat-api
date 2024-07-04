import os
import json
import io
from PIL import Image
from flask import Blueprint, jsonify, request, send_file
from config.openai import client

from utils.serializers import serialize_run_step
from utils.file_utils import determine_content_type
from utils.json_utils import write_to_json, update_run_steps
from routes.operations import create_thread, add_message_to_thread, retrieve_run, get_file_data
from config.logging import logger

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/', methods=['GET'])
def health_check():
    try:
        logger.info("Health check endpoint hit")
        return jsonify({"status": "Ok"}), 200
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/create-thread', methods=['POST'])
def create_thread_endpoint():
    try:
        thread_id = create_thread(client)
        logger.info(f"Created thread with ID: {thread_id}")
        return jsonify({"thread_id": thread_id}), 200
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/add-message', methods=['POST'])
def add_message_endpoint():
    try:
        message = request.json.get('message')
        thread_id = request.json.get('thread_id')
        assistant_id = request.json.get('assistant_id')

        logger.info(f"Adding message to thread: {thread_id}, message: {message}")

        run_id = add_message_to_thread(client, thread_id, message, assistant_id)
        logger.info(f"Created run with ID: {run_id}")

        return jsonify({"run_id": run_id}), 200
    except Exception as e:
        logger.error(f"Error adding message: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/get-run', methods=['POST'])
def get_run_endpoint():
    try:
        thread_id = request.json.get('thread_id')
        run_id = request.json.get('run_id')

        response = retrieve_run(client, thread_id, run_id)
        logger.info(f"Retrieved and serialized run: {run_id} for thread: {thread_id}")

        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error retrieving run: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/get-file', methods=['POST'])
def get_file_endpoint():
    try:
        file_id = request.json.get('file_id')
        if not file_id:
            logger.warning("file_id is required but not provided")
            return jsonify({"error": "file_id is required"}), 400

        file_response = get_file_data(client, file_id)
        logger.info(f"Retrieved and converted file with ID: {file_id}")

        return file_response
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        return jsonify({"error": str(e)}), 500
