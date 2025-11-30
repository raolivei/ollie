#!/bin/bash

# Start Ollama in the background
/bin/ollama serve &
pid=$!

# Wait for Ollama to wake up
sleep 5

echo "Checking for model llama3.1:8b..."
# Check if model exists, if not pull it
if ! /bin/ollama list | grep -q "llama3.1:8b"; then
    echo "Model not found. Pulling llama3.1:8b..."
    /bin/ollama pull llama3.1:8b
else
    echo "Model llama3.1:8b already exists."
fi

# Wait for the process to finish
wait $pid

