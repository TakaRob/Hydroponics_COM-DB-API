# data_processor.py
import sqlite3
import logging
from datetime import datetime, timezone
import config  # Assuming config.py exists
from models import SensorReading # Class with the model of our sensor readings.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database Functions ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        # isolation_level=None for autocommit (simpler for single inserts)
        # or manage transactions explicitly if needed
        conn = sqlite3.connect(config.DATABASE_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # Use Row factory for easier access to columns by name if needed later
        # conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise # Re-raise the exception if connection fails

def initialize_database():
    """Creates the sensor_readings table if it doesn't exist."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                timestamp TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (timestamp, sensor_id, type)
            )
        ''')
        # Add index for faster querying
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sensor_time ON sensor_readings (sensor_id, timestamp DESC);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_type_time ON sensor_readings (type, timestamp DESC);
        ''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

def store_reading(reading: SensorReading):
    """
    Stores a SensorReading object into the database.

    Args:
        reading: A SensorReading object containing the data.

    Returns:
        bool: True if storage was successful, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = ''' INSERT INTO sensor_readings(timestamp, sensor_id, type, value)
                  VALUES(?,?,?,?) '''
        # Use the tuple generated by the SensorReading object
        cursor.execute(sql, reading.to_db_tuple())
        conn.commit()
        logging.debug(f"Stored reading: {reading}")
        return True
    except sqlite3.IntegrityError:
        # Handle cases where the primary key (timestamp, sensor_id, type) might conflict
        # This might happen if readings come in too fast with the same timestamp from the same source
        logging.warning(f"IntegrityError: Could not store duplicate reading: {reading}")
        return False
    except sqlite3.Error as e:
        logging.error(f"Database error storing reading {reading}: {e}")
        # Optionally rollback if not using autocommit
        # if conn:
        #     conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# --- Data Parsing ---

def parse_serial_data(data_line: str) -> SensorReading | None:
    """
    Parses a raw line of serial data into a SensorReading object.
    Expects data in the format defined by ARDUINO_DATA_SEPARATOR
    and order defined by ARDUINO_DATA_ORDER in config.py.

    Args:
        data_line: The raw string received from the serial port.

    Returns:
        A SensorReading object if parsing is successful, None otherwise.
    """
    try:
        parts = data_line.strip().split(config.ARDUINO_DATA_SEPARATOR)
        if len(parts) != len(config.ARDUINO_DATA_ORDER):
            logging.warning(f"Malformed data line (wrong number of parts): {data_line}")
            return None

        # Create a dictionary mapping order element to value
        data_dict = dict(zip(config.ARDUINO_DATA_ORDER, parts))

        # Extract values based on expected keys
        sensor_id = data_dict.get("SensorID")
        sensor_type = data_dict.get("SensorType")
        value_str = data_dict.get("Value")

        if not sensor_id or not sensor_type or value_str is None:
             logging.warning(f"Malformed data line (missing required fields): {data_line}")
             return None

        # Attempt to create a SensorReading object (handles value conversion and validation)
        reading = SensorReading(sensor_id=sensor_id, sensor_type=sensor_type, value=value_str)
        logging.debug(f"Parsed data successfully: {reading}")
        return reading

    except ValueError as e:
        logging.warning(f"Error parsing data line '{data_line}': {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error parsing data line '{data_line}': {e}")
        return None


def get_readings_from_db(limit: int = 100, sensor_id: str | None = None, sensor_type: str | None = None) -> list[dict]:
    """
    Retrieves readings from the database, optionally filtering.

    Args:
        limit: Maximum number of readings to return.
        sensor_id: Filter by sensor ID if provided.
        sensor_type: Filter by sensor type if provided.

    Returns:
        A list of dictionaries, where each dictionary represents a reading.
    """
    conn = None
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row # Get results as dictionary-like rows
        cursor = conn.cursor()

        query = "SELECT timestamp, sensor_id, type, value FROM sensor_readings"
        params = []
        conditions = []

        if sensor_id:
            conditions.append("sensor_id = ?")
            params.append(sensor_id)
        if sensor_type:
            conditions.append("type = ?")
            params.append(sensor_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Inside get_readings_from_db in data_processor.py
        # Add rowid DESC as a secondary sort key for deterministic order
        query += " ORDER BY timestamp DESC, rowid DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert rows to simple dictionaries
        # Note: We are *not* converting back to SensorReading objects here,
        # just returning the raw data structure expected by the API.
        results = [dict(row) for row in rows]
        return results

    except sqlite3.Error as e:
        logging.error(f"Database error fetching readings: {e}")
        return [] # Return empty list on error
    finally:
        if conn:
            conn.close()