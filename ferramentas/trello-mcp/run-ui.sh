#!/bin/bash
# Executa a interface Streamlit do Trello MCP

cd "$(dirname "$0")"
source .venv/bin/activate
streamlit run Trello-app.py --server.runOnSave true
