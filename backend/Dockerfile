# backend/Dockerfile
FROM node:18-alpine as frontend-build

WORKDIR /frontend-build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ .

# Copy the built frontend
COPY --from=frontend-build /frontend-build/dist /app/static

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV PORT=8080

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Updated Gunicorn configuration for Cloud Run
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 300 --keep-alive 120 app:app
