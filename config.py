# config.py

# Serial Port Configuration (for reading from Arduino)
# Linux Example: '/dev/ttyACM0' or '/dev/ttyUSB0'
# Windows Example: 'COM3'
# Use 'python -m serial.tools.list_ports' in terminal to find available ports
SERIAL_PORT = 'COM3'  # *** ADJUST TO YOUR PI'S ARDUINO PORT ***
SERIAL_BAUD_RATE = 9600       # Must match the Arduino's Serial.begin() rate
SERIAL_TIMEOUT = 1            # Seconds to wait for data on serial read

# Data Processing Configuration
# Define the expected structure from Arduino serial (comma-separated)
# Example: "SensorID,SensorType,Value" -> Indices 0, 1, 2
ARDUINO_DATA_ORDER = ["sensor_id", "sensor_type", "value"]
ARDUINO_DATA_SEPARATOR = ","

# Database Configuration
# Store DB inside the 'data' subfolder within the container's working dir
DATABASE_NAME = "data/sensor_data.db" # Relative path inside the app
TABLE_NAME = "readings"


# API Server Configuration (Served FROM the Pi)
API_HOST = "0.0.0.0"  # Listen on all interfaces on the Pi
API_PORT = 5000

# Manual Entry GUI Configuration
MANUAL_ENTRY_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M" # For manual entry GUI timestamp input