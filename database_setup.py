# database_setup.py
import data_processor
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Attempting to initialize the database schema...")
    if data_processor.create_table_if_not_exists():
        logging.info("Database schema initialization successful.")
    else:
        logging.error("Database schema initialization failed.")