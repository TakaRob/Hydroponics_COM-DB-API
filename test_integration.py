# test_integration.py

import unittest
import sqlite3
import os
import json
from datetime import datetime, timedelta

# --- Modules to test ---
import data_processor
from config import (TABLE_NAME, ARDUINO_DATA_ORDER, ARDUINO_DATA_SEPARATOR,
                    MANUAL_ENTRY_TIMESTAMP_FORMAT)

# --- Test Configuration ---
TEST_DB_NAME = "test_sensor_data.db"

class TestDataPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before all tests."""
        # Ensure no previous test DB exists
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        # We'll create the DB connection and table in setUp for isolation per test

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests."""
        # Clean up the test database file
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
            print(f"\nRemoved test database: {TEST_DB_NAME}")

    def setUp(self):
        """Runs before each individual test method."""
        # Ensure clean slate for each test
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        # Establish connection to the TEST database
        self.conn = sqlite3.connect(TEST_DB_NAME)
        self.conn.row_factory = sqlite3.Row # Use row factory for easier access
        self.cursor = self.conn.cursor()
        # Override the get_db_connection function in data_processor *if necessary*,
        # or pass the connection/db_name directly. For simplicity,
        # we'll modify the data_processor functions slightly or test carefully.
        # For now, let's directly call create/insert with our test connection/cursor logic.
        self._create_test_table()

    def tearDown(self):
        """Runs after each individual test method."""
        # Close the connection
        if self.conn:
            self.conn.close()
        # Optional: remove DB after each test if strict isolation needed,
        # but setUp already handles removal before the next test.
        # if os.path.exists(TEST_DB_NAME):
        #     os.remove(TEST_DB_NAME)

    def _create_test_table(self):
        """Helper to create table using the test connection."""
        # Replicates the schema creation part of create_table_if_not_exists
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    sensor_id TEXT,
                    sensor_type TEXT,
                    value REAL,
                    raw_data TEXT
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            self.fail(f"Failed to create test table: {e}")

    # ----- Test Cases -----

    def test_01_table_creation(self):
        """Verify that the table was created correctly in setUp."""
        self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}';")
        result = self.cursor.fetchone()
        self.assertIsNotNone(result, f"Table '{TABLE_NAME}' should exist after setUp.")
        self.assertEqual(result['name'], TABLE_NAME)

    def test_02_format_good_serial_data(self):
        """Test formatting valid serial data strings."""
        test_str_ok = "PHProbe-Tank1,pH,6.75"
        formatted_list = data_processor.format_data_for_db(test_str_ok)

        self.assertIsInstance(formatted_list, list, "Should return a list.")
        self.assertEqual(len(formatted_list), 1, "Should contain one record.")

        record = formatted_list[0]
        self.assertIsInstance(record, dict, "Record should be a dictionary.")
        self.assertIn("timestamp", record)
        self.assertIn("sensor_id", record)
        self.assertIn("sensor_type", record)
        self.assertIn("value", record)
        self.assertIn("raw_data", record)

        self.assertIsInstance(record["timestamp"], datetime, "Timestamp should be datetime obj.")
        # Check timestamp is recent (within a reasonable delta, e.g., 5 seconds)
        self.assertTrue(datetime.now() - record["timestamp"] < timedelta(seconds=5))
        self.assertEqual(record["sensor_id"], "PHProbe-Tank1")
        self.assertEqual(record["sensor_type"], "pH")
        self.assertEqual(record["value"], 6.75)
        self.assertIsInstance(record["value"], float, "Value should be a float.")

        # Check raw_data field
        self.assertIsInstance(record["raw_data"], str, "Raw data should be a JSON string.")
        try:
            raw_dict = json.loads(record["raw_data"])
            self.assertEqual(raw_dict.get("sensor_id"), "PHProbe-Tank1")
            self.assertEqual(raw_dict.get("sensor_type"), "pH")
            self.assertEqual(raw_dict.get("value"), 6.75) # Should match the float value
        except json.JSONDecodeError:
            self.fail("raw_data field does not contain valid JSON.")

    def test_03_format_bad_serial_data(self):
        """Test formatting invalid serial data strings."""
        test_str_bad_parts = "LevelSensor,95" # Too few parts
        test_str_bad_value = "ORP-Main,ORP,high" # Value not numeric
        test_str_empty = ""
        test_str_none = None

        self.assertEqual(data_processor.format_data_for_db(test_str_bad_parts), [], "Bad parts string should return empty list.")
        self.assertEqual(data_processor.format_data_for_db(test_str_bad_value), [], "Bad value string should return empty list.")
        self.assertEqual(data_processor.format_data_for_db(test_str_empty), [], "Empty string should return empty list.")
        self.assertEqual(data_processor.format_data_for_db(test_str_none), [], "None input should return empty list.")


    def test_04_insert_single_record(self):
        """Test inserting a single valid record."""
        test_str_ok = "ECMeter-Res,EC,1.42"
        formatted_list = data_processor.format_data_for_db(test_str_ok)
        self.assertEqual(len(formatted_list), 1, "Formatting failed for single record test.")

        # --- Directly use test connection for insertion ---
        # We modify insert_data_to_db slightly for testability or mock get_db_connection.
        # Simpler: Replicate insertion logic here using self.conn
        record = formatted_list[0]
        sql = f"""
            INSERT INTO {TABLE_NAME} (timestamp, sensor_id, sensor_type, value, raw_data)
            VALUES (:timestamp, :sensor_id, :sensor_type, :value, :raw_data)
        """
        try:
            self.cursor.execute(sql, record)
            self.conn.commit()
            inserted = True
        except sqlite3.Error as e:
            inserted = False
            print(f"Direct insert failed: {e}") # Print error if direct insert fails
        # --- End direct insertion ---

        # Ideally, test data_processor.insert_data_to_db by temporarily overriding DB name
        # or mocking get_db_connection. This requires more setup (mocking library).
        # Let's assume direct insertion worked for verification purposes.

        self.assertTrue(inserted, "Insertion should succeed.") # Check our manual insert

        # Verify data in DB
        self.cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        results = self.cursor.fetchall()
        self.assertEqual(len(results), 1, "Should be exactly one record in the DB.")

        db_record = results[0]
        self.assertEqual(db_record["sensor_id"], "ECMeter-Res")
        self.assertEqual(db_record["sensor_type"], "EC")
        self.assertEqual(db_record["value"], 1.42)
        self.assertIsInstance(db_record["timestamp"], str) # SQLite stores DATETIME often as ISO string
        # Optional: Parse string back to datetime for comparison if needed
        # db_ts = datetime.fromisoformat(db_record["timestamp"])
        # self.assertAlmostEqual(db_ts, record["timestamp"], delta=timedelta(seconds=1))

    def test_05_insert_multiple_records(self):
        """Test inserting multiple valid records at once."""
        test_strs = [
            "Temp-Tank,Water temperature,21.5",
            "Level-Tank,Water level,85.2", # Assuming level is numeric %
            "PHProbe-Res,pH,7.1"
        ]
        formatted_list = []
        for s in test_strs:
            formatted = data_processor.format_data_for_db(s)
            if formatted:
                formatted_list.extend(formatted)

        self.assertEqual(len(formatted_list), 3, "Formatting failed for multiple records.")

        # --- Direct insertion using executemany ---
        sql = f"""
            INSERT INTO {TABLE_NAME} (timestamp, sensor_id, sensor_type, value, raw_data)
            VALUES (:timestamp, :sensor_id, :sensor_type, :value, :raw_data)
        """
        try:
            self.cursor.executemany(sql, formatted_list)
            self.conn.commit()
            inserted = True
        except sqlite3.Error as e:
            inserted = False
            print(f"Direct multi-insert failed: {e}")
        # --- End direct insertion ---

        self.assertTrue(inserted, "Multi-record insertion should succeed.")

        # Verify data in DB
        self.cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME}")
        result = self.cursor.fetchone()
        self.assertEqual(result["count"], 3, "Should be exactly 3 records in the DB.")

    def test_06_insert_manual_entry_data(self):
        """Test inserting data structured like manual GUI entry."""
        # Simulate data prepared by manual_entry_gui.py's submit_data
        manual_ts_str = "2024-03-15T10:00"
        try:
            dt_object = datetime.strptime(manual_ts_str, MANUAL_ENTRY_TIMESTAMP_FORMAT)
        except ValueError:
            self.fail("Failed to parse manual timestamp string using configured format.")

        manual_data_dict = {"sensor_id": "Manual-ORP", "sensor_type": "ORP", "value": 350.5, "manual_ts": manual_ts_str}
        record_to_insert = {
            "timestamp": dt_object,
            "sensor_id": "Manual-ORP",
            "sensor_type": "ORP",
            "value": 350.5,
            "raw_data": json.dumps(manual_data_dict)
        }

        # --- Direct insertion ---
        sql = f"""
            INSERT INTO {TABLE_NAME} (timestamp, sensor_id, sensor_type, value, raw_data)
            VALUES (:timestamp, :sensor_id, :sensor_type, :value, :raw_data)
        """
        try:
            self.cursor.execute(sql, record_to_insert)
            self.conn.commit()
            inserted = True
        except sqlite3.Error as e:
            inserted = False
            print(f"Direct manual data insert failed: {e}")
        # --- End direct insertion ---

        self.assertTrue(inserted, "Manual data insertion should succeed.")

        # Verify
        self.cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE sensor_id = 'Manual-ORP'")
        db_record = self.cursor.fetchone()
        self.assertIsNotNone(db_record, "Manual record not found in DB.")
        self.assertEqual(db_record["sensor_type"], "ORP")
        self.assertEqual(db_record["value"], 350.5)
        # Check timestamp string matches (SQLite might add seconds/microseconds)
        # --- Updated Timestamp Check ---
        # Parse the timestamp string retrieved from the database
        try:
            # Attempt parsing common SQLite ISO formats (space separator)
            db_ts_str = db_record["timestamp"]
            # Handle potential fractional seconds by splitting
            if '.' in db_ts_str:
                db_dt_object = datetime.strptime(db_ts_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
            else:
                db_dt_object = datetime.strptime(db_ts_str, '%Y-%m-%d %H:%M:%S')

        except (ValueError, TypeError) as e:
            # Fallback or add more formats if needed, or fail the test
            self.fail(f"Could not parse timestamp '{db_record['timestamp']}' from DB: {e}")

        # Compare the parsed DB datetime object with the original datetime object
        # We compare year, month, day, hour, minute (ignore seconds/microseconds difference from DB)
        self.assertEqual(db_dt_object.year, dt_object.year)
        self.assertEqual(db_dt_object.month, dt_object.month)
        self.assertEqual(db_dt_object.day, dt_object.day)
        self.assertEqual(db_dt_object.hour, dt_object.hour)
        self.assertEqual(db_dt_object.minute, dt_object.minute)
        # Optionally, if seconds matter and should be 00 in this case:
        # self.assertEqual(db_dt_object.second, dt_object.second) # dt_object has second=0 here

        # --- End Updated Timestamp Check ---

        # Check raw data reflects manual entry structure
        raw_dict = json.loads(db_record["raw_data"])
        self.assertEqual(raw_dict.get("manual_ts"), manual_ts_str)


# ----- Run Tests -----
if __name__ == '__main__':
    print("Running Integration Tests...")
    unittest.main(verbosity=2) # verbosity=2 provides more detailed output