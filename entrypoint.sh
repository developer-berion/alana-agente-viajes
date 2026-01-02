#!/bin/bash

# Start FastAPI in the background
echo "Starting FastAPI..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Wait for API to be ready
echo "Waiting for API..."
until curl -s http://localhost:8000/health; do
  sleep 1
done

echo "API is up! Starting Streamlit..."
# Start Streamlit on the port provided by Cloud Run ($PORT)
streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
