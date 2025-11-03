#!/bin/bash
# Get Current File Directory
cd $(dirname "$0")
echo "Updating bot in $(pwd)"
echo "Using $(./.venv/bin/python --version)"
./.venv/bin/pip install -r requirements.txt
