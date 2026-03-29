FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from backend folder
# We use context . so backend is passed as context root, but wait docker-compose says context is . and dockerfile is ./backend/Dockerfile
# So COPY backend matches the context
COPY backend /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
