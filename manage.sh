#!/bin/bash
# Smart Home Services Manager Wrapper
# Automatically activates virtual environment and runs manage_services.py

cd "$(dirname "$0")"
source venv/bin/activate
export HA_URL=http://192.168.0.81:8123
export OLLAMA_URL=http://100.94.114.43:11434

python3 manage_services.py "$@"