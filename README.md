# Product Update Summarizer

A simple web application that summarizes product updates and patch notes from any URL.

## Features

- **Single URL Processing**: Submit a product update or patch notes URL to get a summary
- **Basic Content Extraction**: Extract text content from the provided URL
- **Simple Date Filtering**: Filter content based on a cutoff date
- **Summary Generation**: Use AI to generate a concise summary of the updates
- **Single-Page Experience**: Simple web interface with URL input field and date selector

## Tech Stack

- **Frontend**: React, Vite
- **Backend**: Flask, Python
- **AI**: Google Gemini AI
- **Web Scraping**: BeautifulSoup4, Requests

## Setup

### Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- Google Gemini AI API key

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Gemini AI API key:
   ```
   # Copy the example file
   cp .env.example .env
   
   # Then edit .env and add your actual API key
   GEMINI_API_KEY=your_actual_api_key_here
   ```

   > **Important**: The `.env` file contains sensitive information and is not committed to the repository. Make sure to keep your API key secure.

5. Run the backend server:
   ```
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

## Usage

1. Open your browser and navigate to `http://localhost:5173`
2. Enter a product update or patch notes URL
3. Optionally, select a cutoff date to filter updates
4. Click "Summarize Updates" to generate a summary

## Future Enhancements

- Support for multiple URLs
- Database of existing products
- User accounts and history tracking
- More sophisticated content extraction for specific sites
- Advanced date filtering and parsing 