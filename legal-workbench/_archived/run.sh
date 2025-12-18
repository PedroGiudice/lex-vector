#!/bin/bash
# run.sh - Cloud Run entrypoint for Legal Workbench Streamlit app

# Default to port 8080 if PORT is not set
PORT=${PORT:-8080}

# Run Streamlit on the specified port
# Headless mode is enabled for environments without a browser.
# server.enableCORS=false is a security measure for Cloud Run.
streamlit run app.py --server.port=$PORT --server.headless=true --server.enableCORS=false
