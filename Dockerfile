FROM python:3.10-slim

# Install minimal system dependencies for Playwright (no Xvfb needed for headless)
RUN apt-get update && apt-get install -y \
    libgbm-dev \
    libnss3 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium)
RUN playwright install chromium
RUN playwright install-deps

COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true

# Start with Gunicorn (for Render) or python (for local)
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "wsgi:application"]

