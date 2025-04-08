# serial_data_logger.py

import time
import logging
import signal # For graceful shutdown
import serial_reader # Our new module
import data_processor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global flag for shutdown ---
keep_running = True

def signal_handler(signum, frame):
    """Handles signals like Ctrl+C for graceful shutdown."""
    global keep_running
    logging.info(f"Received signal {signum}. Shutting down...")
    keep_running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler) # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Handle kill/system shutdown

def run_serial_listener():
    """Main loop to listen to Arduino via serial and log data."""
    logging.info("Starting serial data logger...")

    # Ensure the database table exists before starting the loop
    if not data_processor.create_table_if_not_exists():
        logging.error("Failed to initialize database table. Exiting.")
        return

    serial_conn = None
    while keep_running:
        try:
            # Attempt to connect/reconnect if connection is lost
            if serial_conn is None or not serial_conn.is_open:
                logging.info("Serial connection lost or not established. Attempting to reconnect...")
                if serial_conn and serial_conn.is_open: # Attempt clean close first
                    try: serial_conn.close()
                    except Exception: pass
                serial_conn = serial_reader.setup_serial_connection()
                if serial_conn is None:
                    logging.warning("Connection attempt failed. Retrying in 10 seconds...")
                    time.sleep(10)
                    continue # Go to start of loop to retry connection
                else:
                     logging.info("Reconnected successfully.")


            # Read data from the established connection
            raw_line = serial_reader.read_line_from_serial(serial_conn)

            if raw_line is not None:
                # Process the received line
                formatted_data = data_processor.format_data_for_db(raw_line)

                if formatted_data: # Check if formatting was successful
                    data_processor.insert_data_to_db(formatted_data)
                # else: Formatting errors are logged within format_data_for_db

            # Small delay to prevent tight loop if readline timeout is 0 or very short
            # Adjust based on how frequently Arduino sends data vs SERIAL_TIMEOUT
            # If timeout is 1s, this sleep might not be strictly needed but doesn't hurt much
            time.sleep(0.1)

        except Exception as e:
            # Catch unexpected errors in the main loop
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            # Attempt to close connection on error, will retry reconnecting next loop
            if serial_conn and serial_conn.is_open:
                try: serial_conn.close()
                except Exception: pass
            serial_conn = None
            time.sleep(5) # Wait a bit before retrying after unexpected error

    # --- Cleanup after loop exits ---
    logging.info("Serial logger loop finished.")
    if serial_conn and serial_conn.is_open:
        try:
            serial_conn.close()
            logging.info("Serial connection closed.")
        except Exception as e:
            logging.error(f"Error closing serial port on exit: {e}")

if __name__ == "__main__":
    run_serial_listener()
    logging.info("Program finished.")