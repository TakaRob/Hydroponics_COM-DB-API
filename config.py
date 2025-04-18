# config.py
import os

# Serial Port Configuration

SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
#SERIAL_PORT = '/dev/ttyACM0'  # --- MUST SET --- e.g., '/dev/ttyACM0', '/dev/ttyUSB0', 'COM3' For Laptop 'COM3'
#SERIAL_PORT = 'COM3'  # --- MUST SET --- e.g., '/dev/ttyACM0', '/dev/ttyUSB0', 'COM3' For Laptop 'COM3'
SERIAL_BAUD_RATE = 9600       # Match Arduino's Serial.begin() rate
SERIAL_TIMEOUT = 1            # Read timeout in seconds
SERIAL_RETRY_DELAY = 5        # Second# s to wait before retrying connection

# --- Database Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATABASE_NAME = os.path.join(DATA_DIR, 'sensor_data.db') # <-- Path inside container
os.makedirs(DATA_DIR, exist_ok=True)


# Arduino Data Format (Crucial for parsing)
# Defines the order of fields separated by ARDUINO_DATA_SEPARATOR
# *** MUST contain 'SensorID', 'SensorType', and 'Value' ***
ARDUINO_DATA_ORDER = ["SensorID", "SensorType", "Value"]
ARDUINO_DATA_SEPARATOR = ","

# Database Configuration
DATABASE_NAME = 'sensor_data.db'

# API Server Configuration
API_HOST = '0.0.0.0'  # Listen on all network interfaces
API_PORT = 5000

# Add other configurations as needed