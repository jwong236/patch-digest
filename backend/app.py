from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv
import os
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
# Configure CORS with more specific settings
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

import routes

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
