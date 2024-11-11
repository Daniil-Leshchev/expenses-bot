# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim-bookworm

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Set the working directory
WORKDIR /app
COPY . /app

# Copy .env file if it exists
# The || true at the end ensures the command doesn’t fail if .env is missing
COPY .env /app/.env || true

# Export environment variables from .env if the file exists
RUN if [ -f /app/.env ]; then export $(cat /app/.env | xargs); fi

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

LABEL org.opencontainers.image.source="https://github.com/daniil-leshchev/google-sheets-expenses-bot"

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "main.py"]