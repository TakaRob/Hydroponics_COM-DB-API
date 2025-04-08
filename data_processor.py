# data_processor.py

import sqlite3
import json
import logging
from datetime import datetime
from config import (DATABASE_NAME, TABLE_NAME,
                    ARDUINO_DATA_ORDER, ARDUINO_DATA_SEPARATOR) # Import new config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database Functions --- (get_db_connection, create_table_if_not_exists remain the same)
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def create_table_if_not_exists():
    """Creates the sensor readings table if it doesn't exist (Schema unchanged)."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                sensor_id TEXT,
                sensor_type TEXT,
                value REAL,
                raw_data TEXT
            )
        """)
        conn.commit()
        logging.info(f"Table '{TABLE_NAME}' checked/created successfully.")
        # Optional migration check can remain if relevant from previous states
        # ... (migration code omitted for brevity, same as before) ...
        return True
    except sqlite3.Error as e:
        logging.error(f"Error creating/checking table '{TABLE_NAME}': {e}")
        return False
    finally:
        if conn: conn.close()


# --- Data Processing and Insertion ---

def format_data_for_db(raw_serial_string):
    """
    Parses a raw string received from Arduino serial, validates it,
    adds a timestamp, and formats it for database insertion.

    Args:
        raw_serial_string (str): The raw string line read from serial
                                 (e.g., "SensorID,SensorType,Value").

    Returns:
        list: A list containing a single dictionary formatted for DB insertion,
              or an empty list if parsing/validation fails.
    """
    if not raw_serial_string or not isinstance(raw_serial_string, str):
        logging.warning("format_data_for_db received invalid input (empty or not string).")
        return []

    parts = raw_serial_string.strip().split(ARDUINO_DATA_SEPARATOR)
    expected_parts = len(ARDUINO_DATA_ORDER)

    if len(parts) != expected_parts:
        logging.warning(f"Skipping record: Incorrect number of parts. "
                        f"Expected {expected_parts}, Got {len(parts)}. Data: '{raw_serial_string}'")
        return []

    try:
        # Create a dictionary from parts based on configured order
        data_dict = {}
        for i, key in enumerate(ARDUINO_DATA_ORDER):
            data_dict[key] = parts[i].strip() # Store initially as strings

        # --- Validate and Convert ---
        sensor_id = data_dict.get("sensor_id")
        sensor_type = data_dict.get("sensor_type")
        value_str = data_dict.get("value")

        if not all([sensor_id, sensor_type, value_str]):
             logging.warning(f"Skipping record: Missing required fields "
                            f"(sensor_id, sensor_type, value). Data: '{raw_serial_string}'")
             return []

        try:
            value_float = float(value_str)
        except ValueError:
             logging.warning(f"Skipping record: Invalid numeric value for 'value'. "
                             f"Got '{value_str}'. Data: '{raw_serial_string}'")
             return []

        # --- Generate Timestamp ---
        timestamp_obj = datetime.now()

        # --- Prepare final record ---
         # Store the *parsed* dictionary as raw_data for consistency
        raw_data_dict_for_json = {
             "sensor_id": sensor_id,
             "sensor_type": sensor_type,
             "value": value_float # Store float here too
        }

        record = {
            "timestamp": timestamp_obj, # Use the generated timestamp
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "value": value_float,
            "raw_data": json.dumps(raw_data_dict_for_json) # Store parsed dict as JSON string
        }

        return [record] # Return as a list containing the single record

    except Exception as e:
        logging.error(f"Unexpected error formatting record from string '{raw_serial_string}': {e}")
        return []


# --- insert_data_to_db remains the same ---
def insert_data_to_db(formatted_records):
    """Inserts a list of formatted sensor data records into the database."""
    if not formatted_records:
        # This is normal if formatting failed, not necessarily an error to log here
        # logging.info("No valid records formatted for insertion.")
        return True

    conn = get_db_connection()
    if not conn: return False

    inserted_count = 0
    try:
        cursor = conn.cursor()
        sql = f"""
            INSERT INTO {TABLE_NAME} (timestamp, sensor_id, sensor_type, value, raw_data)
            VALUES (:timestamp, :sensor_id, :sensor_type, :value, :raw_data)
        """
        cursor.executemany(sql, formatted_records)
        conn.commit()
        inserted_count = len(formatted_records)
        logging.info(f"Successfully inserted {inserted_count} record(s) into '{TABLE_NAME}'.")
        return True
    except sqlite3.Error as e:
        logging.error(f"Database insertion error: {e}")
        try: conn.rollback()
        except sqlite3.Error as rb_err: logging.error(f"Rollback failed: {rb_err}")
        return False
    finally:
        if conn: conn.close()

# Example usage (for testing this module directly)
if __name__ == "__main__":
    print("Initializing database and table...")
    if create_table_if_not_exists():
        print("Database table setup complete.")

        # Example serial strings
        test_str_ok = "PHProbe-Tank1,pH,6.75"
        test_str_ec = "ECMeter-Res,EC,1.42"
        test_str_temp = "Temp-Tank,Water temperature,21.5"
        test_str_bad_parts = "LevelSensor,95" # Too few parts
        test_str_bad_value = "ORP-Main,ORP,high" # Value not numeric

        print(f"\nTesting format: '{test_str_ok}'")
        formatted_ok = format_data_for_db(test_str_ok)
        print(formatted_ok)

        print(f"\nTesting format: '{test_str_ec}'")
        formatted_ec = format_data_for_db(test_str_ec)
        print(formatted_ec)

        print(f"\nTesting format: '{test_str_temp}'")
        formatted_temp = format_data_for_db(test_str_temp)
        print(formatted_temp)

        print(f"\nTesting format (bad parts): '{test_str_bad_parts}'")
        formatted_bad_parts = format_data_for_db(test_str_bad_parts)
        print(formatted_bad_parts) # Should be []

        print(f"\nTesting format (bad value): '{test_str_bad_value}'")
        formatted_bad_value = format_data_for_db(test_str_bad_value)
        print(formatted_bad_value) # Should be []

        print("\nTesting insertion (good records):")
        combined_good = formatted_ok + formatted_ec + formatted_temp
        if combined_good:
             insert_data_to_db(combined_good)
        else:
             print("No valid data formatted for insertion.")
    else:
        print("Failed to set up database table.")