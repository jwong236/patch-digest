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
TOKENS_PER_REQUEST = 1500


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

    estimated_tokens = len(prompt.split()) * 1.3

    if estimated_tokens > TOKENS_PER_REQUEST:
        words = prompt.split()
        truncated_words = words[: int(TOKENS_PER_REQUEST / 1.3)]
        prompt = " ".join(truncated_words) + "... [truncated]"
        print(f"Prompt truncated to approximately {TOKENS_PER_REQUEST} tokens")

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


def get_html_selectors(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        prompt = f"""
        You are an expert at analyzing HTML structure to find selectors for extracting links.
        
        I need you to analyze this HTML and determine TWO things:
        
        1. FIRST, verify if this page is a valid patch notes catalogue by looking for:
           - Page titles or headings containing "patch notes", "release notes", "changelog", etc.
           - Content sections about updates, patches, or releases
           - Lists or collections of patch notes or updates
           
        2. SECOND, if it IS a valid patch notes catalogue, determine the CSS selectors that would help extract links to patch notes.
           Look for patterns in the HTML that indicate links to patch notes, such as:
           - Links containing words like "patch", "update", "release", "notes", "changelog"
           - Links within sections titled "Updates", "Releases", "Patch Notes", etc.
           - Links with dates in their text, URL or nearby elements
           
           IMPORTANT: The selectors should ONLY target links to actual patch note pages, not links to other language versions or categories.
           For example, if the page has links like:
           - "Patch 13.10 Notes" -> INCLUDE (this is a patch note)
           - "Patch Notes (AR)" or "Patch Notes (ES)" -> EXCLUDE (these are language selectors)
           - "Categories" or "Tags" -> EXCLUDE (these are navigation links)
           
           For League of Legends specifically, look for:
           - Links with href containing "/news/game-updates/patch-" or similar patterns
           - Links with aria-label containing "Patch" and "Notes"
           - Links with class names that might indicate article cards or featured content
           - Elements with data-testid attributes like "articlefeaturedcard-component"
        
        Return ONLY a JSON object with these fields:
        - "is_valid": true/false indicating if this page appears to be a valid patch notes catalogue
        - "link_selector": The CSS selector to find the links to patch notes (only if is_valid is true)
        - "pagination_selector": The CSS selector for the "next page" link (if pagination exists, only if is_valid is true)
        - "verification_reason": A brief explanation of why you determined this is or isn't a patch notes catalogue
        
        Here's the HTML to analyze:
        
        {soup.prettify()[:8000]}
        """

        result = call_gemini_with_retry(prompt)

        try:
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", result)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result

            selectors = json.loads(json_str)

            if not selectors.get("is_valid", False) or not selectors.get(
                "link_selector"
            ):
                if "leagueoflegends.com" in url and "patch-notes" in url:
                    print("Using fallback selectors for League of Legends")
                    selectors = {
                        "is_valid": True,
                        "link_selector": "a[href*='/news/game-updates/patch-'], a[aria-label*='Patch'][aria-label*='Notes']",
                        "pagination_selector": "a[aria-label='Next page'], a.next-page, a[rel='next']",
                        "verification_reason": "Fallback selectors for League of Legends patch notes",
                    }

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
    max_pages = 5

    while current_url and page_count < max_pages:
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

    selectors = get_html_selectors(url)

    if "error" in selectors:
        return jsonify({"error": selectors["error"]}), 400

    if not selectors.get("is_valid", False):
        return (
            jsonify(
                {
                    "error": "The provided URL does not appear to be a valid patch notes catalogue"
                }
            ),
            400,
        )

    patch_note_urls = get_all_patch_note_urls(url, selectors)

    if not patch_note_urls:
        return jsonify({"error": "No patch note links found in the catalogue"}), 400

    max_patch_notes = 3
    if len(patch_note_urls) > max_patch_notes:
        patch_note_urls = patch_note_urls[:max_patch_notes]
        print(f"Limiting to {max_patch_notes} patch notes to avoid rate limits")

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
