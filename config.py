# config.py
import os

# ----------------------
# Serial Port Configuration
# ----------------------
# To override the serial port (e.g., for Docker or different OS), set the SERIAL_PORT environment variable.
# Example: docker run ... --env SERIAL_PORT=/dev/ttyUSB0 ...
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
# To hardcode for development, uncomment one of the following (but don't commit secrets or local paths!):
# SERIAL_PORT = '/dev/ttyACM0'  # Linux/Raspberry Pi typical
# SERIAL_PORT = 'COM3'          # Windows typical
SERIAL_BAUD_RATE = 9600       # Must match Arduino's Serial.begin() rate
SERIAL_TIMEOUT = 1            # Serial read timeout (seconds)
SERIAL_RETRY_DELAY = 5        # Seconds to wait before retrying connection

# ----------------------
# Database Configuration
# ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATABASE_NAME = os.path.join(DATA_DIR, 'sensor_data.db') # Path for DB file (inside container or local)
os.makedirs(DATA_DIR, exist_ok=True)

# SECURITY NOTE: Do not expose your database file or path in public endpoints or error messages.

# ----------------------
# Arduino Data Format (Parsing)
# ----------------------
# ARDUINO_DATA_ORDER: List of field names in the order sent by Arduino over serial.
# *** MUST contain 'SensorID', 'SensorType', and 'Value' ***
# If your Arduino sends extra fields (e.g., timestamp), add them here and update the parser accordingly.
# Example for custom order: ["SensorType", "SensorID", "Value"]
#
# JSON compatibility: If you want to output JSON with different field names or structure,
#   - Change ARDUINO_DATA_ORDER to match your data
#   - Update any code that builds/parses SensorReading objects or serializes to JSON
ARDUINO_DATA_ORDER = ["SensorID", "SensorType", "Value"]
ARDUINO_DATA_SEPARATOR = ","  # Change if your Arduino uses a different delimiter (e.g., ';' or '\t')

# ----------------------
# API Server Configuration
# ----------------------
API_HOST = '0.0.0.0'  # Listen on all network interfaces (for Docker/production)
API_PORT = 5000       # Change if you want the API on a different port

# ----------------------
# How to add/change config:
# ----------------------
# - Add new variables here as needed (e.g., LOG_LEVEL, ALLOWED_ORIGINS, etc.)
# - For secrets (API keys, passwords), use environment variables and NEVER commit them to git.
#
# Example for environment variable usage:
#   MY_SECRET = os.environ.get('MY_SECRET', 'default_value')

# ----------------------
# End of config.py
# ----------------------