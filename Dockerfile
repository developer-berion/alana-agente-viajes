FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# Supervisor needs to be installed via pip (added to requirements)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Cloud Run sets the PORT environment variable
ENV PORT=8080

CMD ["./entrypoint.sh"]
