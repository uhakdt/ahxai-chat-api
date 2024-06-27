import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from openai import OpenAI
from log_config import setup_logger

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

logger = setup_logger()
