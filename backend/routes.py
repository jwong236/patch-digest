from app import app, supabase
from flask import request, jsonify


@app.route("/api/hello", methods=["GET"])
def hello_world():
    return jsonify(message="Hello from Flask!")


@app.route("/api/test-supabase", methods=["GET"])
def test_supabase():
    response = supabase.table("products").select("*").execute()
    return jsonify(response.data)
