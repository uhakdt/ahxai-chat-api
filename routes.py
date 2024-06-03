from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

CORS(app)


@app.route('/', methods=['GET'])
def root():
  try:
    return jsonify({"status": "OK"}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500