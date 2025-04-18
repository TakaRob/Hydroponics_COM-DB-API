# serial_data_logger.py
import time
import logging
import signal
import sys
import serial

import config
import serial_reader # Assuming serial_reader.py exists and has connect/read functions
import data_processor # Uses the updated data_processor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global flag to control the main loop
running = True

def signal_handler(sig, frame):
    """Handles termination signals gracefully."""
    global running
    logging.info("Termination signal received. Shutting down gracefully...")
    running = False

# Register signal handlers for SIGINT (Ctrl+C) and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main function to read from serial and store data."""
    logging.info("Starting Serial Data Logger...")

    # Initialize database (ensure table exists)
    data_processor.initialize_database()

    ser = None
    while running: # Loop until signal handler sets running to False
        try:
            if ser is None or not ser.is_open:
                logging.info(f"Attempting to connect to serial port {config.SERIAL_PORT}...")
                # Add a timeout (e.g., 1 second) to prevent blocking indefinitely if no data arrives
                ser = serial.Serial(config.SERIAL_PORT, config.SERIAL_BAUD_RATE, timeout=1)

                if ser:
                    logging.info(f"Successfully connected to {config.SERIAL_PORT}.")
                else:
                    logging.warning(f"Failed to connect. Retrying in {config.SERIAL_RETRY_DELAY} seconds...")
                    time.sleep(config.SERIAL_RETRY_DELAY)
                    continue # Skip to the next iteration

            # Read data
            # Check if data is available (optional but good practice with timeout=0)
            # Since we have a timeout in serial.Serial, readline() will wait
            # if ser.in_waiting > 0: # You might or might not need this check depending on timeout behavior

            line_bytes = ser.readline()  # Read bytes until newline or timeout

            # Decode bytes to string. Use 'utf-8' typically.
            # 'errors='ignore'' prevents crashing on weird bytes, but might hide issues.
            # 'errors='replace'' is another option.
            line = line_bytes.decode('utf-8', errors='ignore').strip()

            logging.debug(f"Received line: {line_bytes}")  # Log raw bytes if needed for debugging

            if line:
                logging.debug(f"Received raw data: {line}")
                # Parse the data using the updated processor function
                sensor_reading = data_processor.parse_serial_data(line)

                if sensor_reading:
                    # Store the SensorReading object
                    success = data_processor.store_reading(sensor_reading)
                    if not success:
                        logging.warning(f"Failed to store reading: {sensor_reading}")
                # If parse_serial_data returned None, it logged the error already

            else:
                # No data received, maybe short timeout occurred, just loop again
                pass

        except serial.SerialException as e:
            logging.error(f"Serial communication error: {e}")
            if ser and ser.is_open:
                ser.close()
            ser = None # Force reconnection attempt
            logging.info(f"Attempting reconnection in {config.SERIAL_RETRY_DELAY} seconds...")
            time.sleep(config.SERIAL_RETRY_DELAY)
        except KeyboardInterrupt: # Should be caught by signal handler, but good practice
             logging.info("KeyboardInterrupt caught. Exiting.")
             break # Exit the while loop
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}") # Log full traceback
            # Decide if to retry or exit on unexpected errors
            time.sleep(5) # Wait a bit before retrying

    # Cleanup
    if ser and ser.is_open:
        ser.close()
        logging.info("Serial port closed.")
    logging.info("Serial Data Logger stopped.")

if __name__ == "__main__":
    # Add a check in config for required settings
    required_configs = ['SERIAL_PORT', 'SERIAL_BAUD_RATE', 'DATABASE_NAME', 'ARDUINO_DATA_ORDER', 'ARDUINO_DATA_SEPARATOR']
    missing_configs = [cfg for cfg in required_configs if not hasattr(config, cfg)]
    if missing_configs:
        logging.error(f"Configuration error: Missing required settings in config.py: {', '.join(missing_configs)}")
        sys.exit(1)

    if "Value" not in config.ARDUINO_DATA_ORDER or \
       "SensorID" not in config.ARDUINO_DATA_ORDER or \
       "SensorType" not in config.ARDUINO_DATA_ORDER:
        logging.error("Configuration error: ARDUINO_DATA_ORDER must contain 'Value', 'SensorID', and 'SensorType'.")
        sys.exit(1)

    main()