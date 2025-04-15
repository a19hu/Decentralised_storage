#!/bin/bash

# Script to deregister a storage node from the decentralized storage system

# Function to show usage
show_usage() {
    echo "Usage: $0 <node_id> [--remove]"
    echo "  node_id   : ID of the node to deregister (e.g., 'ashu' or 'node3')"
    echo "  --remove  : Optional flag to completely remove the node container and volume"
    echo ""
    echo "Example: $0 ashu --remove"
    exit 1
}

# Check if node_id parameter is provided
if [ $# -lt 1 ]; then
    show_usage
fi

NODE_ID=$1
REMOVE_FLAG=0

# Check if --remove flag is set
if [ $# -gt 1 ] && [ "$2" == "--remove" ]; then
    REMOVE_FLAG=1
fi

# Get container ID for the node
CONTAINER_ID=$(docker ps -a --filter "label=com.docker.compose.service=${NODE_ID}" --format "{{.ID}}")

# If no container found, try searching by environment variable
if [ -z "$CONTAINER_ID" ]; then
    CONTAINER_ID=$(docker ps -a --filter "env=NODE_ID=${NODE_ID}" --format "{{.ID}}")
fi

# If still no container found, try searching by name
if [ -z "$CONTAINER_ID" ]; then
    CONTAINER_ID=$(docker ps -a --filter "name=${NODE_ID}" --format "{{.ID}}")
fi

# If still no container found, list running containers and ask user to select
if [ -z "$CONTAINER_ID" ]; then
    echo "No container found with node ID '${NODE_ID}'"
    echo "Here are the running storage node containers:"
    docker ps --filter "ancestor=storage_node" --format "{{.ID}}\t{{.Names}}\t{{.Status}}"
    echo ""
    echo "Please specify one of these container IDs instead of the node ID"
    exit 1
fi

# Stop the container
echo "Stopping storage node container ${CONTAINER_ID}..."
docker stop ${CONTAINER_ID}

# If --remove flag is set, remove the container and volume
if [ $REMOVE_FLAG -eq 1 ]; then
    echo "Removing storage node container and volume..."
    
    # Get volume name
    VOLUME_NAME=$(docker inspect ${CONTAINER_ID} --format '{{ range .Mounts }}{{ if eq .Type "volume" }}{{ .Name }}{{ end }}{{ end }}')
    
    # Remove container
    docker rm ${CONTAINER_ID}
    
    # Remove volume if found
    if [ ! -z "$VOLUME_NAME" ]; then
        echo "Removing volume ${VOLUME_NAME}..."
        docker volume rm ${VOLUME_NAME}
    fi
fi

echo "Storage node ${NODE_ID} has been deregistered."
echo ""
echo "Note: The node information may still be cached in the coordinator's memory."
echo "The node will be completely removed from listings after the coordinator is restarted,"
echo "or after its health check timeout expires (if implemented)." 