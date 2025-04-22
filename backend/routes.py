from app import app
from flask import request, jsonify
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import time
import random
import json
import re
from datetime import datetime, timedelta

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

REQUESTS_PER_MINUTE = 30
REQUESTS_PER_DAY = 1000000
MAX_PATCH_NOTES = 1


class APIRateLimiter:
    def __init__(self):
        self.minute_requests = []
        self.day_requests = []
        self.lock = False

    def can_make_request(self):
        now = datetime.now()

        self.minute_requests = [
            t for t in self.minute_requests if now - t < timedelta(minutes=1)
        ]
        self.day_requests = [
            t for t in self.day_requests if now - t < timedelta(days=1)
        ]

        if len(self.minute_requests) >= REQUESTS_PER_MINUTE:
            oldest_minute = self.minute_requests[0]
            wait_time = 60 - (now - oldest_minute).total_seconds()
            return False, max(1, int(wait_time))

        if len(self.day_requests) >= REQUESTS_PER_DAY:
            oldest_day = self.day_requests[0]
            wait_time = 86400 - (now - oldest_day).total_seconds()
            return False, max(60, int(wait_time))

        return True, 0

    def record_request(self):
        now = datetime.now()
        self.minute_requests.append(now)
        self.day_requests.append(now)


rate_limiter = APIRateLimiter()


def call_gemini_with_retry(prompt, max_retries=3):
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    for attempt in range(max_retries):
        can_request, wait_time = rate_limiter.can_make_request()

        if not can_request:
            if attempt < max_retries - 1:
                print(
                    f"Rate limit reached. Waiting {wait_time} seconds before retry..."
                )
                time.sleep(wait_time)
                continue
            else:
                raise Exception(
                    f"Rate limit reached. Try again in {wait_time} seconds."
                )

        try:
            rate_limiter.record_request()

            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_message = str(e)

            if "quota" in error_message.lower():
                raise Exception(
                    "API quota exceeded. Please check your billing details."
                )

            if attempt < max_retries - 1:
                time.sleep(2)
                continue

            raise e


def verify_patch_notes_catalogue(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        prompt = "Analyze this HTML and determine if it's a patch notes catalogue.\n\n"
        prompt += f"HTML to analyze:\n{soup.prettify()}\n\n"
        prompt += "Return a JSON object with: is_valid (boolean), verification_reason (string)."

        result = call_gemini_with_retry(prompt)

        try:
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", result)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result

            verification = json.loads(json_str)
            return verification

        except json.JSONDecodeError:
            return {
                "error": "Failed to parse AI response as JSON",
                "raw_response": result,
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch URL: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def get_html_selectors(url, reference_url=None):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        reference_pattern = None
        if reference_url:
            try:
                ref_response = requests.get(reference_url)
                ref_response.raise_for_status()

                from urllib.parse import urlparse

                parsed_url = urlparse(reference_url)
                path = parsed_url.path

                if "/patch-" in path:
                    reference_pattern = path.split("/patch-")[0] + "/patch-"
                elif "/news/" in path:
                    reference_pattern = "/news/"

                print(f"Reference pattern extracted: {reference_pattern}")
            except Exception as e:
                print(f"Error extracting reference pattern: {str(e)}")

        prompt = "Find CSS selectors for patch note links in this HTML.\n\n"

        if reference_url and reference_pattern:
            prompt += f"Reference URL: {reference_url}\nPattern to look for: {reference_pattern}\n\n"

        prompt += f"HTML to analyze:\n{soup.prettify()}\n\n"
        prompt += "Return a JSON object with: link_selector (string), pagination_selector (string if exists)."

        result = call_gemini_with_retry(prompt)

        try:
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", result)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result

            selectors = json.loads(json_str)
            return selectors

        except json.JSONDecodeError:
            return {
                "error": "Failed to parse AI response as JSON",
                "raw_response": result,
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch URL: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def get_all_patch_note_urls(url, selectors):
    all_urls = []
    current_url = url
    page_count = 0

    while current_url:
        try:
            response = requests.get(current_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            links = soup.select(selectors["link_selector"])

            for link in links:
                href = link.get("href")
                if href:
                    if href.startswith("/"):
                        from urllib.parse import urljoin

                        href = urljoin(url, href)
                    all_urls.append(href)

            next_page = None
            if "pagination_selector" in selectors and selectors["pagination_selector"]:
                next_page_elem = soup.select_one(selectors["pagination_selector"])
                if next_page_elem and next_page_elem.get("href"):
                    next_page = next_page_elem.get("href")
                    if next_page.startswith("/"):
                        from urllib.parse import urljoin

                        next_page = urljoin(url, next_page)

            current_url = next_page
            page_count += 1

            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {current_url}: {str(e)}")
            break
        except Exception as e:
            print(f"Error processing page {current_url}: {str(e)}")
            break

    if len(all_urls) > MAX_PATCH_NOTES:
        print(
            f"Found {len(all_urls)} patch notes, limiting to {MAX_PATCH_NOTES} most recent"
        )
        all_urls = all_urls[:MAX_PATCH_NOTES]

    return all_urls


def summarize_patch_note(url):
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

        prompt = f"""
        You are a helpful assistant that summarizes product updates and patch notes.
        Focus on key changes, additions, removals, and fixes.
        Be concise and clear.

        IMPORTANT FORMATTING RULES:
        - Use only asterisks (*) for bullet points, no dashes or other markers
        - Each main bullet should be immediately followed by its text, no extra spaces
        - Each sub-bullet should be indented with exactly 4 spaces
        - No empty lines between bullets
        - No trailing spaces
        - No newlines within bullet text (use single line format)

        Here's the content to summarize:

        {text[:8000]}
        """

        summary = call_gemini_with_retry(prompt)

        return {"url": url, "summary": summary}

    except requests.exceptions.RequestException as e:
        return {"url": url, "error": f"Failed to fetch URL: {str(e)}"}
    except Exception as e:
        return {"url": url, "error": f"An error occurred: {str(e)}"}


@app.route("/api/summarize", methods=["OPTIONS"])
def handle_options():
    return "", 200


@app.route("/api/summarize", methods=["POST"])
def summarize_updates():
    data = request.json

    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data["url"]
    reference_url = data.get("reference_url")

    verification = verify_patch_notes_catalogue(url)

    if "error" in verification:
        return jsonify({"error": verification["error"]}), 400

    if not verification.get("is_valid", False):
        return (
            jsonify(
                {
                    "error": "The provided URL does not appear to be a valid patch notes catalogue",
                    "reason": verification.get("verification_reason", "Unknown reason"),
                }
            ),
            400,
        )

    selectors = get_html_selectors(url, reference_url)

    if "error" in selectors:
        return jsonify({"error": selectors["error"]}), 400

    if not selectors.get("link_selector"):
        return (
            jsonify({"error": "Could not determine selectors for patch note links"}),
            400,
        )

    patch_note_urls = get_all_patch_note_urls(url, selectors)

    if not patch_note_urls:
        return jsonify({"error": "No patch note links found in the catalogue"}), 400

    summaries = []
    for patch_url in patch_note_urls:
        try:
            summary = summarize_patch_note(patch_url)
            summaries.append(summary)

            time.sleep(3)
        except Exception as e:
            print(f"Error summarizing {patch_url}: {str(e)}")
            summaries.append({"url": patch_url, "error": str(e)})

    return jsonify(
        {
            "catalogue_url": url,
            "patch_notes": summaries,
            "total_found": len(patch_note_urls),
            "processed": len(summaries),
        }
    )
