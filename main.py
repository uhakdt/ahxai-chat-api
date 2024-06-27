from flask_setup import app
from routes import api

app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=False, port=8283, host='0.0.0.0')