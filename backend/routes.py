from app import app
from flask import request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai
import os
from dateutil import parser

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

@app.route("/api/summarize", methods=["OPTIONS"])
def handle_options():
    return "", 200

@app.route("/api/summarize", methods=["POST"])
def summarize_updates():
    data = request.json
    
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400
    
    url = data["url"]
    cutoff_date_str = data.get("cutoff_date")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        if cutoff_date_str:
            try:
                cutoff_date = parser.parse(cutoff_date_str)
                text = f"Please summarize updates since {cutoff_date_str}. Here's the content: {text}"
            except:
                return jsonify({"error": "Invalid date format"}), 400
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        You are a helpful assistant that summarizes product updates and patch notes.
        Focus on key changes, additions, removals, and fixes.
        Be concise and clear.
        
        Here's the content to summarize:
        
        {text}
        """
        
        response = model.generate_content(prompt)
        summary = response.text
        
        return jsonify({
            "summary": summary,
            "original_url": url
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
