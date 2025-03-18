from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)


@app.route("/api/hello", methods=["GET"])
def hello_world():
    return jsonify(message="Hello from Flask!")


# frontend_folder = os.path.join(os.getcwd(), "..", "frontend")
# dist_folder = os.path.join(frontend_folder, "dist")


# # Serve the built frontend
# @app.route("/", defaults={"filename": ""})
# @app.route("/<path:filename>")
# def index(filename):
#     if not filename:
#         filename = "index.html"
#     return send_from_directory(dist_folder, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
