FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# Supervisor needs to be installed via pip (added to requirements)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose ports for API (8000) and Frontend (8501)
# Cloud Run only maps one port to the public URL (usually based on PORT env var).
# We need to decide which one is the "entrypoint".
# If we want the UI to be the main entry, we expose 8080 mapping to 8501.
# BUT Request asks for "Nodo Soberano" UI.
# So $PORT should map to Streamlit.
# HOWEVER, Streamlit also needs to talk to API. 
# If they are in the same container, UI talks to localhost:8000.
# The external user sees Streamlit.
# So we run Streamlit on $PORT or default 8080.
# Supervisord makes this tricky with dynamic PORT env var.
# Better strategy: Entrypoint script replaces port in supervisord config or command.

# For simplicity in this demo, we'll assume Cloud Run default port 8080 maps to Streamlit
# and we hardcode API to 8000 (internal).

CMD ["supervisord", "-c", "supervisord.conf"]
