#!/bin/bash
# Get Current File Directory
cd $(dirname "$0")
echo "Starting bot in $(pwd)"
echo "Using $(./.venv/bin/python --version)"
./.venv/bin/python src/main.py
