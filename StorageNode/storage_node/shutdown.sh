#!/bin/bash

# This script ensures proper deregistration when stopping the container
# It's used as a pre-stop hook in Docker Compose

NODE_ID=${NODE_ID:-"unknown"}
COORDINATOR_URL=${COORDINATOR_URL:-"http://localhost:5001"}

echo "Gracefully shutting down storage node ${NODE_ID}..."

# Call the deregister endpoint directly to ensure it happens
curl -X POST -H "Content-Type: application/json" -d "{\"node_id\":\"${NODE_ID}\"}" ${COORDINATOR_URL}/deregister

# Give the deregistration request time to complete
sleep 2

echo "Storage node ${NODE_ID} deregistered."

# Send SIGTERM to the main app process (PID 1 in container)
kill -TERM 1

# Wait for process to terminate
wait 