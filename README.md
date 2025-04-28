# Patch Digest

A web application that provides concise summaries of product updates and patch notes using AI.

## Features

- Summarizes product updates and patch notes from any URL using Google's Gemini AI
- Clean, modern UI
- Real-time processing of content
- Responsive design for all devices

## Live Demo

The application is live and can be accessed at:
https://patch-digest-344920797300.us-central1.run.app

## How It Works

1. Enter a URL to a patch notes catalogue (a webpage containing links to multiple patch notes)
2. Optionally provide a reference patch note URL to help identify similar links
3. Select how many patch notes you want to summarize (up to 10)
4. Click "Summarize Updates" to generate concise summaries
5. View the AI-generated summaries in an accordion format

## Deployment

The application is deployed using Google Cloud Run. The deployment process is automated using Cloud Build.

### Architecture

- Frontend: React + Vite
- Backend: Flask
- AI: Google Gemini API
- Deployment: Google Cloud Run
- Secrets Management: Google Secret Manager

## License

This project is licensed under the MIT License - see the LICENSE file for details. 