# test_integration.py
import pytest
import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
import sys
import threading

# Ensure project root is in path (if tests are in a subfolder)
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Test Setup ---
# Use a temporary database for testing
TEST_DB_NAME = "test_sensor_data.db"

# Make sure the modules under test use the test DB
# We'll use pytest's monkeypatch fixture for this.

# Import modules AFTER potentially modifying config path or setting up test env
import config
# IMPORTANT: Import api_server AFTER patching config if needed,
# because it reads config on import level for app setup.
# We will import it within the fixture that needs it.
import data_processor
from models import SensorReading

# --- Fixtures ---

@pytest.fixture(scope="function") # Run for each test function
def test_db(monkeypatch):
    """Fixture to create and clean up a temporary test database."""
    db_path = os.path.join(os.path.dirname(__file__), TEST_DB_NAME)

    # --- Critical: Patch config BEFORE modules using it are used ---
    # Monkeypatch the DATABASE_NAME in the config module *before*
    # data_processor functions (like initialize_database) are called.
    monkeypatch.setattr(config, 'DATABASE_NAME', db_path)
    # Also ensure data_processor uses the patched config if it imported DATABASE_NAME directly
    # (Best practice: data_processor should always use config.DATABASE_NAME)
    monkeypatch.setattr(data_processor.config, 'DATABASE_NAME', db_path)


    # Clean up any old test database file before starting
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"\nRemoved old test database: {db_path}")

    # Initialize the database schema using the (now patched) config path
    try:
        print(f"\nInitializing test database: {config.DATABASE_NAME}")
        data_processor.initialize_database()
        assert os.path.exists(db_path)
        print("Test database initialized.")
    except Exception as e:
        pytest.fail(f"Failed to initialize test database {db_path}: {e}")


    yield db_path  # Provide the path to the test function

    # Teardown: Clean up the database file after the test function runs
    print(f"\nCleaning up test database: {db_path}")
    # Add a small delay/retry for cleanup on Windows potentially
    time.sleep(0.1)
    try:
        if os.path.exists(db_path):
            # Ensure connections are closed (in case of errors in tests)
            # This is tricky as connections are function-scoped in data_processor
            # Relying on Python's garbage collection or explicit close is ideal
            os.remove(db_path)
            print("Test database removed.")
    except Exception as e:
        print(f"Warning: Could not remove test database {db_path}: {e}")

@pytest.fixture(scope="function")
def api_client(test_db, monkeypatch):
    """Fixture to get a Flask test client configured for the test database."""
    # Need to import api_server HERE, after config is patched by test_db fixture
    import api_server

    # Ensure the Flask app instance inside api_server uses the patched config
    monkeypatch.setattr(api_server.config, 'DATABASE_NAME', test_db) # test_db holds the patched path
    monkeypatch.setattr(api_server.data_processor.config, 'DATABASE_NAME', test_db)

    # Configure the app for testing
    api_server.app.config['TESTING'] = True
    api_server.app.config['DATABASE'] = test_db # Optional: Explicitly pass db path if app uses it

    # Create a test client
    with api_server.app.test_client() as client:
        yield client # Provide the test client to the test function

    # Teardown (if any specific client teardown needed) happens automatically by exiting 'with'

# --- Test Functions ---

def test_database_initialization(test_db):
    """Verify that the database file is created and has the correct table."""
    assert os.path.exists(test_db)
    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_readings';")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'sensor_readings'
        # Check if columns exist (optional detailed check)
        cursor.execute("PRAGMA table_info(sensor_readings);")
        columns = {row[1] for row in cursor.fetchall()}
        assert columns == {'timestamp', 'sensor_id', 'type', 'value'}
    except sqlite3.Error as e:
        pytest.fail(f"Database check failed: {e}")
    finally:
        if conn:
            conn.close()

def test_parse_valid_serial_data():
    """Test parsing a correctly formatted serial string."""
    # Assumes default config: ["SensorID", "SensorType", "Value"], separator ","
    line = "PHProbe-Tank1,pH,7.01"
    reading = data_processor.parse_serial_data(line)
    assert reading is not None
    assert isinstance(reading, SensorReading)
    assert reading.sensor_id == "PHProbe-Tank1"
    assert reading.sensor_type == "pH"
    assert reading.value == 7.01
    assert isinstance(reading.timestamp, datetime)

def test_parse_invalid_serial_data():
    """Test parsing various incorrect serial strings."""
    assert data_processor.parse_serial_data("Too,Few,Parts") is None # Default expects 3
    assert data_processor.parse_serial_data("ID,Type,NotANumber") is None
    assert data_processor.parse_serial_data("") is None
    assert data_processor.parse_serial_data("OnlyOnePart") is None
    # Test with different config order (if needed, use monkeypatch on config)

def test_store_and_retrieve_reading(test_db):
    """Test storing a reading via data_processor and retrieving it directly."""
    now = datetime.now(timezone.utc)
    reading_in = SensorReading(
        sensor_id="ECMeter-Tank1",
        sensor_type="EC",
        value=1.55,
        timestamp=now
    )

    # Store the reading
    success = data_processor.store_reading(reading_in)
    assert success is True

    # Retrieve readings
    readings_out = data_processor.get_readings_from_db(limit=10)

    assert len(readings_out) == 1
    reading_out_dict = readings_out[0]

    # Compare relevant fields (timestamps might have slight format differences)
    assert reading_out_dict['sensor_id'] == reading_in.sensor_id
    assert reading_out_dict['type'] == reading_in.sensor_type
    assert reading_out_dict['value'] == reading_in.value
    # Compare timestamp (handle potential string formatting from DB vs datetime object)
    # Convert stored ISO string back to comparable datetime object
    retrieved_ts = datetime.fromisoformat(reading_out_dict['timestamp'])
    # Allow for minor differences if storage/retrieval truncates microseconds
    assert abs(retrieved_ts - reading_in.timestamp) < timedelta(seconds=1)


def test_api_status_endpoint(api_client):
    """Test the /status API endpoint."""
    response = api_client.get('/status')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}

def test_api_get_readings_empty(api_client):
    """Test fetching readings from an empty database via API."""
    response = api_client.get('/readings')
    assert response.status_code == 200
    assert response.json == []

def test_api_store_and_get_single_reading(api_client, test_db):
    """Test storing a reading (via data_processor) and retrieving via API."""
    now = datetime.now(timezone.utc)
    reading_in = SensorReading(
        sensor_id="TempProbe-Room",
        sensor_type="Air temperature",
        value=22.5,
        timestamp=now
    )
    # Store directly using data_processor (API doesn't have a POST endpoint)
    success = data_processor.store_reading(reading_in)
    assert success is True

    # Retrieve via API
    response = api_client.get('/readings?limit=5')
    assert response.status_code == 200
    readings_out = response.json
    assert len(readings_out) == 1

    reading_out_dict = readings_out[0]
    assert reading_out_dict['sensor_id'] == reading_in.sensor_id
    assert reading_out_dict['type'] == reading_in.sensor_type
    assert reading_out_dict['value'] == reading_in.value
    retrieved_ts = datetime.fromisoformat(reading_out_dict['timestamp'])
    assert abs(retrieved_ts - reading_in.timestamp) < timedelta(seconds=1)


def test_api_get_readings_filtering(api_client, test_db):
    """Test API filtering by limit, sensor_id, and type."""
    # Store multiple readings
    t1 = datetime.now(timezone.utc) - timedelta(minutes=10)
    t2 = datetime.now(timezone.utc) - timedelta(minutes=5)
    t3 = datetime.now(timezone.utc) - timedelta(minutes=1)

    readings_to_store = [
        SensorReading("pH-1", "pH", 6.8, t1),
        SensorReading("EC-1", "EC", 1.4, t1),
        SensorReading("pH-1", "pH", 6.9, t2),
        SensorReading("Temp-1", "Water temperature", 21.0, t2),
        SensorReading("pH-1", "pH", 7.0, t3),
        SensorReading("EC-1", "EC", 1.5, t3),
    ]
    for r in readings_to_store:
        data_processor.store_reading(r)

    # Test limit
    response = api_client.get('/readings?limit=4')
    assert response.status_code == 200
    assert len(response.json) == 4
    # Check if latest are returned (implicit check of ORDER BY timestamp DESC)
    assert response.json[0]['sensor_id'] == 'EC-1' # EC-1 @ t3
    assert response.json[1]['sensor_id'] == 'pH-1'  # pH-1 @ t3

    # Test sensor_id filter
    response = api_client.get('/readings?sensor_id=EC-1')
    assert response.status_code == 200
    assert len(response.json) == 2
    assert all(r['sensor_id'] == 'EC-1' for r in response.json)

    # Test type filter
    response = api_client.get('/readings?type=pH')
    assert response.status_code == 200
    assert len(response.json) == 3
    assert all(r['type'] == 'pH' for r in response.json)

    # Test combined filter
    response = api_client.get('/readings?sensor_id=pH-1&type=pH')
    assert response.status_code == 200
    assert len(response.json) == 3 # All pH readings are from pH-1
    assert all(r['sensor_id'] == 'pH-1' and r['type'] == 'pH' for r in response.json)

    # Test combined filter with limit
    response = api_client.get('/readings?type=pH&limit=2')
    assert response.status_code == 200
    assert len(response.json) == 2
    # Check latest two pH readings
    assert response.json[0]['value'] == 7.0 # pH @ t3
    assert response.json[1]['value'] == 6.9 # pH @ t2


# Example of how to simulate the logger's core loop action
def test_simulated_logger_run(api_client, test_db):
    """Simulate receiving data, processing, storing, and verify via API."""
    serial_lines = [
        "ID_A,TypeX,10.1", # t0
        "ID_B,TypeY,20.2", # t1
        "ID_A,TypeX,10.5", # t2
    ]

    stored_timestamps = []

    # Simulate processing loop
    for line in serial_lines:
        reading = data_processor.parse_serial_data(line)
        assert reading is not None
        success = data_processor.store_reading(reading)
        assert success is True
        stored_timestamps.append(reading.timestamp)
        time.sleep(0.01) # Ensure slightly different timestamps if needed

    # Verify via API
    response = api_client.get('/readings?limit=10')
    assert response.status_code == 200
    results = response.json
    assert len(results) == 3

    # Check if results match input (in reverse time order)
    assert results[0]['sensor_id'] == 'ID_A' and results[0]['value'] == 10.5
    assert results[1]['sensor_id'] == 'ID_B' and results[1]['value'] == 20.2
    assert results[2]['sensor_id'] == 'ID_A' and results[2]['value'] == 10.1

    # Compare timestamp of the last retrieved item (oldest)
    retrieved_ts = datetime.fromisoformat(results[2]['timestamp'])
    assert abs(retrieved_ts - stored_timestamps[0]) < timedelta(seconds=1)