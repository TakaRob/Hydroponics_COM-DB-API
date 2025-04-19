# Use an official Python runtime available for amd64 and arm
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install basics (sqlite3 client is useful for debugging inside container)
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the data directory exists inside the container
# While VOLUME implies the directory, creating it explicitly doesn't hurt
# and ensures correct permissions might be set by WORKDIR user if applicable.
RUN mkdir -p /app/data

# ---> Add the VOLUME instruction here <---
# Mark the /app/data directory as containing externally mountable volume data
VOLUME /app/data


# Expose the API port
EXPOSE 5000

# Command to run both scripts
# Run logger in the background (&)
# Run API server in the foreground (keeps container running)
# Use sh -c to handle the background process correctly
CMD ["sh", "-c", "python serial_data_logger.py & python api_server.py"]