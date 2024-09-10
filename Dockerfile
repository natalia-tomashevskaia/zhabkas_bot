# Use the official slim image for Python 3.9
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code into the Docker image
COPY . .
EXPOSE 8080
# Create a new user to run the application
RUN useradd -m botuser
USER botuser

# Set entry point to run the bot
CMD ["python", "zhabkas_bot.py"]
