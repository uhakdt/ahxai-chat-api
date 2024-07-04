import os
from flask import Flask, Blueprint
from flask_cors import CORS
from routes.routes import api

app = Flask(__name__)
CORS(app)

app.register_blueprint(api)
