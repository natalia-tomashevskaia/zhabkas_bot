FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
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

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code into the Docker image
COPY . .

# Run the bot
CMD ["python", "zhabkas_bot.py"]
