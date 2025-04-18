# serial_reader.py

import serial
import logging
import time
from config import SERIAL_PORT, SERIAL_BAUD_RATE, SERIAL_TIMEOUT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_serial_connection():
    """Attempts to establish a connection to the Arduino via serial."""
    ser = None
    try:
        logging.info(f"Attempting to connect to Arduino on {SERIAL_PORT} at {SERIAL_BAUD_RATE} baud...")
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)
        time.sleep(2) # Allow time for connection and Arduino reset cycle
        if ser.is_open:
            logging.info(f"Successfully connected to {SERIAL_PORT}")
            ser.flushInput() # Clear any stale data in the buffer
            return ser
        else:
            logging.error(f"Serial port {SERIAL_PORT} is not open after attempt.")
            return None
    except serial.SerialException as e:
        logging.error(f"Serial connection error on {SERIAL_PORT}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during serial setup: {e}")
        return None

def read_line_from_serial(serial_connection):
    """
    Reads a single line of data from the provided serial connection.

    Args:
        serial_connection (serial.Serial): An active PySerial connection object.

    Returns:
        str: The decoded data line (stripped of whitespace),
             or None if no data read, timeout occurs, or error happens.
    """
    if not serial_connection or not serial_connection.is_open:
        logging.error("Serial connection is not available or not open.")
        return None

    try:
        if serial_connection.in_waiting > 0:
            line = serial_connection.readline()
            # Attempt to decode using common encodings
            try:
                decoded_line = line.decode('utf-8').strip()
            except UnicodeDecodeError:
                try:
                    decoded_line = line.decode('ascii', errors='ignore').strip()
                    logging.warning(f"Decoded with ASCII (potential data loss) from: {line}")
                except Exception as decode_err:
                     logging.error(f"Failed to decode serial data: {line}. Error: {decode_err}")
                     return None

            if decoded_line:
                logging.debug(f"Raw data received: '{decoded_line}'")
                return decoded_line
            else:
                # Empty line received, often happens, can ignore
                logging.debug("Empty line received from serial.")
                return None
        else:
            # No data waiting, timeout likely occurred in readline if configured > 0
            logging.debug("No data waiting on serial port.")
            return None
    except serial.SerialException as e:
        logging.error(f"Serial error during read: {e}")
        # Consider attempting to close/reopen connection here or in main loop
        return None
    except OSError as e:
         logging.error(f"OS error during serial read (device disconnected?): {e}")
         return None
    except Exception as e:
        logging.error(f"Unexpected error during serial read: {e}")
        return None

# Example Test (run this file directly)
if __name__ == "__main__":
    print("Testing serial reader...")
    ser = setup_serial_connection()
    if ser:
        print("Connection successful. Waiting for data for 10 seconds (Press Ctrl+C to stop)...")
        try:
            for _ in range(100): # Read for ~10 seconds (100 * 0.1s)
                data = read_line_from_serial(ser)
                if data:
                    print(f"Read: {data}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping test.")
        finally:
            if ser.is_open:
                ser.close()
                print("Serial connection closed.")
    else:
        print("Failed to connect to serial port.")