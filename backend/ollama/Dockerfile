# Use the official Ollama image
FROM ollama/ollama:latest

# Set working directory (not required but keeps things organized)
WORKDIR /root/.ollama

# Expose API port
EXPOSE 11434

# Start Ollama when the container runs
ENTRYPOINT ["ollama", "serve"]
