#!/bin/bash
# Make sure to make this file executable: chmod +x run.sh
export FLASK_APP=app.py
export FLASK_ENV=development # This enables debug mode and auto-reloading
echo "Starting Flask server..."
echo "Access the application at http://127.0.0.1:8888"
flask run --port=8888