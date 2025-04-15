# config.py (Example Snippet)

# Serial Port Configuration
SERIAL_PORT = 'COM3'   #'/dev/ttyACM0'  # --- MUST SET --- e.g., '/dev/ttyACM0', '/dev/ttyUSB0', 'COM3'
SERIAL_BAUD_RATE = 9600       # Match Arduino's Serial.begin() rate
SERIAL_TIMEOUT = 1            # Read timeout in seconds
SERIAL_RETRY_DELAY = 5        # Seconds to wait before retrying connection

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