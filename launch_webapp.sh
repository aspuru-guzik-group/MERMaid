#!/bin/bash

fuser -k 8000/tcp

# Run FastAPI backend
echo "Starting FastAPI backend."
uvicorn webapp.fastapi_app:app --host 127.0.0.1 --port 8000 --reload &

# Run Streamlit frontend
echo "Starting Streamlit frontend."
streamlit run webapp/streamlit_app.py