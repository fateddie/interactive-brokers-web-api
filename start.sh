#!/bin/bash

# Start IB Gateway in background
cd gateway && sh bin/run.sh root/conf.yaml &

# Wait for Gateway to start
sleep 5

# Start Flask application
cd /app/webapp
export FLASK_APP=app.py
export FLASK_DEBUG=1
export FLASK_PORT=5056

# Start Flask application
python3 -m flask run --host=0.0.0.0 --port=${FLASK_PORT}