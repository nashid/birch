#!/bin/bash

# Script to run Ollama server, pull a model, execute d4j_code_repair.py, and clean up

# Exit on errors
set -e

# Check if enough arguments are passed
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <model_name> <mode> <multihunk>"
    echo "Example: ./run_ollama_d4j.sh llama3.1 4 yes"
    exit 1
fi

# Parse arguments
MODEL_NAME=$1
MODE=$2
MULTIHUNK=$3

# Step 1: Install Ollama (if not already installed)
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing..."

    # Install Ollama
    if [ -f /etc/os-release ]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "Cannot detect Linux distribution. Please install Ollama manually."
        exit 1
    fi
fi

# Step 2: Start Ollama Server in the background using nohup
echo "Starting Ollama server..."
nohup ollama serve > ollama_server.log 2>&1 &
OLLAMA_PID=$!
sleep 5  # Allow server to start

# Step 3: Define API_HOST (Defaulted to localhost:11434) Reference: https://github.com/ollama/ollama/blob/main/docs/faq.md
API_HOST="http://localhost:11434"
echo "Using API Host: $API_HOST"

# Step 4: Pull the specified model
echo "Pulling the model: $MODEL_NAME..."
ollama pull "$MODEL_NAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to pull the model '$MODEL_NAME'. Terminating script."
    kill $OLLAMA_PID
    exit 1
fi

# Step 5: Run the Python script with arguments
echo "Running d4j_code_repair.py..."
python d4j_code_repair.py --mode "$MODE" --model "ollama/$MODEL_NAME" --multihunk "$MULTIHUNK" --api_host "$API_HOST"

# Step 6: Cleanup: Kill the Ollama server process
echo "Terminating Ollama server..."
kill $OLLAMA_PID

# Verify if the process has been terminated
sleep 2  # Allow time for the process to terminate
if ps -p $OLLAMA_PID > /dev/null; then
    echo "Ollama server still running. Forcefully terminating..."
    kill -9 $OLLAMA_PID
    echo "Ollama server forcefully terminated."
else
    echo "Ollama server successfully terminated."
fi

echo "All processes cleaned up."
