from app import app
from flask import request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai
import os
from dateutil import parser

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC5kYEKx1oy8mCPgOOciqMTg2nt8u10w-Y")
genai.configure(api_key=GEMINI_API_KEY)

# Handle OPTIONS request for CORS preflight
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
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract text content (this is a simple approach - can be improved for specific sites)
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Remove blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Filter by date if cutoff date is provided
        if cutoff_date_str:
            try:
                cutoff_date = parser.parse(cutoff_date_str)
                # This is a simplified approach - in a real app, you'd need more sophisticated date extraction
                # For MVP, we'll just pass the text to the AI and let it handle the filtering
                text = f"Please summarize updates since {cutoff_date_str}. Here's the content: {text}"
            except:
                return jsonify({"error": "Invalid date format"}), 400
        
        # Generate summary using Gemini AI
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
