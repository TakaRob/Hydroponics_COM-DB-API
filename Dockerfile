# Use an official Python runtime as a parent image
# Choose a version compatible with your code and pyserial/flask
# Add '-slim' for a smaller image size
FROM python:3.11-slim

# Set environment variables (optional but good practice)
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents python from writing .pyc files
ENV PYTHONUNBUFFERED=1
# Force stdout/stderr streams to be unbuffered

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (pyserial might need some)
# For Debian/Ubuntu based images (like python:3.11-slim):
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*
# (Check pyserial docs if you encounter issues, but often not needed for basic use)

# Copy just the requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create the data directory within the container image (optional, volume mount will create it too)
# RUN mkdir data

# Expose the port the API server runs on (from config.py)
EXPOSE 5000

# --- Define the default command ---
# Option 1: Run only the serial logger by default
# CMD ["python", "serial_data_logger.py"]

# Option 2: Run only the API server by default
CMD ["python", "api_server.py"]

# Option 3: (More advanced) Use an entrypoint script or supervisor to run both.
# For now, pick one default (like the API) and we'll run the logger separately or use docker-compose later.