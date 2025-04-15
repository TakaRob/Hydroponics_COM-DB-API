# database_setup.py
import sqlite3
import logging
import config # Get DB name from config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup():
    """Initializes the database schema."""
    conn = None
    try:
        logging.info(f"Initializing database: {config.DATABASE_NAME}")
        conn = sqlite3.connect(config.DATABASE_NAME)
        cursor = conn.cursor()

        # Drop table if it exists (optional, for clean setup during dev)
        # cursor.execute("DROP TABLE IF EXISTS sensor_readings")
        # logging.info("Dropped existing sensor_readings table (if any).")

        # Create sensor_readings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                timestamp TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (timestamp, sensor_id, type)
            )
        ''')
        logging.info("Created sensor_readings table (if it didn't exist).")

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sensor_time ON sensor_readings (sensor_id, timestamp DESC);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_type_time ON sensor_readings (type, timestamp DESC);
        ''')
        logging.info("Created indexes (if they didn't exist).")

        conn.commit()
        logging.info("Database setup complete.")

    except sqlite3.Error as e:
        logging.error(f"Database setup error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup()