FROM python:3.11-slim

# Install ffmpeg for audio conversion
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App
COPY . .

ENV PYTHONUNBUFFERED=1
# Enable CORS by default for cross-origin frontend
ENV ENABLE_CORS=true

# Start the WSGI app
CMD ["sh", "-c", "gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT:-8000} app:application"]

