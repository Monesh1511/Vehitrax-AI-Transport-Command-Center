FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and other ML packages
RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Fix missing libGL dependency here to avoid busting pip cache
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

# Copy application code from ml folder
COPY ml /app

CMD ["python", "pipeline.py"]
