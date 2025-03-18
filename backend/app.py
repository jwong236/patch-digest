from flask import Flask, jsonify, send_from_directory
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
supabase: Client = create_client(supabase_url, supabase_key)

# frontend_folder = os.path.join(os.getcwd(), "..", "frontend")
# dist_folder = os.path.join(frontend_folder, "dist")


# # Serve the built frontend
# @app.route("/", defaults={"filename": ""})
# @app.route("/<path:filename>")
# def index(filename):
#     if not filename:
#         filename = "index.html"
#     return send_from_directory(dist_folder, filename)


import routes

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
