FROM ollama/ollama:latest

# Expose the API port
EXPOSE 11434

# Create a script to pull the model on startup if not present
# We can't easily pull during build because the daemon needs to be running.
# So we'll wrap the entrypoint.

COPY ./scripts/start-ollama.sh /start-ollama.sh
RUN chmod +x /start-ollama.sh

ENTRYPOINT ["/start-ollama.sh"]

