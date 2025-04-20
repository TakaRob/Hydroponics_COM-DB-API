# Hydroponics Logger & API — Docker-First

**This project is now distributed primarily as a ready-to-use Docker image.**

- No complicated setup.
- No need to install Python or dependencies.
- No code or config changes required for most users.
- Works on Raspberry Pi or any Linux/WSL2/Windows system with Docker.

## Quick Start (Docker)

# First time users go to SETUP.md
# If running on a non-linux system, go to setup_appendix.md

# MAKE SURE TO CHECK SETUP.md if anything happens, like the serial port not working or if you want avahi enabled.

1. **Plug in your Arduino** to the machine (Raspberry Pi or PC running Docker).
2. **Pull and run the image:**
   ```bash
   docker pull takajirobson/rasppardapi:latest
   docker run --rm -it \
     --device=/dev/ttyACM0 \
     --env SERIAL_PORT=/dev/ttyACM0 \
     -p 5000:5000 \
     -v hydroponics-db-data:/app/data \
     takajirobson/rasppardapi:latest
   ```
   - For Windows/WSL2/usbipd, see [`setup_appendix.md`](./setup_appendix.md) for serial port bridging.
3. **Test the API:**
   ```bash
   curl http://localhost:5000/readings
   ```

---

## If you want to change the sensor readings, make sure to change
- SensorReading in models.py
- sensor_readings in database_setup.py
- sensor_id in data_processor.py
- sensor_id in api_server.py
- ARDUINO_DATA_ORDER in config.py



---

## Project Structure (For Reference Only)
- `config.py`: Serial port, baud rate, data format. **Defaults work for most users.**
- `models.py`, `data_processor.py`, `serial_reader.py`: Data handling logic (inside the image).
- `api_server.py`, `serial_data_logger.py`: API and logger logic (run automatically in Docker).
- `manual_entry_gui.py`: Optional manual entry GUI (requires desktop, not needed for headless use).
- `setup.md`, `setup_appendix.md`: Full and advanced setup guides.

---

## API Endpoints (Default)
- `GET /readings`: Fetch sensor readings. Optional query params: `limit`, `sensor_id`, `type`.
- `GET /status`: Health check.

---


## Troubleshooting & Customization
- See [`setup.md`](./setup.md) and [`setup_appendix.md`](./setup_appendix.md) for:
  - Windows/WSL2/usbipd/COM port bridging
  - Changing serial port or device
  - Advanced configuration
- For the test Arduino code example, see arduinosintest.txt

---

## Project Structure

-   `config.py`: Configuration settings (Serial Port, Baud Rate, Database name, API port, Arduino data format). 
-   `requirements.txt`: Python dependencies (`Flask`, `pyserial`).
-   `models.py`: Defines data structures, primarily the `SensorReading` class which represents a single, structured sensor measurement.
-   `serial_reader.py`: Helper module for handling serial communication with the Arduino.
-   `data_processor.py`: Parses raw serial data into `SensorReading` objects, handles database interactions (storage and retrieval).
-   `database_setup.py`: (Optional but Recommended) Script to explicitly initialize the database schema. Can be run once initially.
-   `api_server.py`: Runs a Flask-based REST API server (on the Pi) to query the database.
-   `serial_data_logger.py`: Main script to continuously listen to the serial port, process data using `data_processor`, and store it via `data_processor`. 
-   `manual_entry_gui.py`: A GUI application (runnable on Pi desktop) for manually entering sensor data (creates `SensorReading` objects).
-   `.gitignore`: Standard Git ignore file.
-   `README.md`: This file.

**Quick summary for legacy/manual setup:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/TakaRob/HydroponicsRaspi-Api.git # Replace with your actual repo URL if different
    cd HydroponicsRaspi-Api
    ```
2.  **(Recommended) Use Docker!** See `setup.md` for containerized instructions for both Pi and Windows/WSL2.
3.  **Or, set up a virtual environment (manual Python):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # To deactivate later: deactivate
    pip install -r requirements.txt
    ```
4.  **Configure the application:**
    - Edit `config.py` as before for serial port, baud rate, and Arduino data format. set up the serial port to the right serial port, check device manager ex: 'COM3' if running on windows.
5.  **Set up the Arduino:**
    -   Connect the Arduino to the Raspberry Pi via USB.
    -   Upload Arduino code that reads your sensors and prints the data to the Serial port. Each complete reading should be on a new line (`println`). The format must match `ARDUINO_DATA_SEPARATOR` and the fields must be in the order specified by `ARDUINO_DATA_ORDER`.
    -   *Example Arduino `loop()` snippet (matching default config):*
        ```c++
        void loop() {
          // Read your sensors
          float pHValue = readPHSensor();
          float ECValue = readECSensor();
          float tempValue = readTempSensor();

          // Print each reading on a new line in the expected format: "SensorID,SensorType,Value"
          Serial.print("PHProbe-Tank1,pH,"); // SensorID, SensorType,
          Serial.println(pHValue);           // Value (println adds newline)

          Serial.print("ECMeter-Tank1,EC,");
          Serial.println(ECValue);

          Serial.print("TempProbe-Tank1,Water temperature,");
          Serial.println(tempValue);

          delay(60000); // Example: Wait 60 seconds before sending next batch
        }
        ```
        *(Adjust Sensor IDs, types, reading functions, and delay as needed)*
6.  **Permissions (Linux/Pi):** You might need to add your user to the `dialout` group to access the serial port:
    ```bash
    sudo usermod -a -G dialout $USER
    ```

## Running the Application

### Manual Python (Legacy)

1.  **Initialize the Database (Run once):**
    ```bash
    python database_setup.py
    ```
2.  **Run the Serial Data Logger:**
    ```bash
    python serial_data_logger.py
    ```
3.  **Run the API Server:**
    ```bash
    python api_server.py
    ```
4.  **Run the Manual Entry GUI (Optional, requires Desktop Environment):**
    ```bash
    python manual_entry_gui.py
    ```

## API Endpoints

-   `GET /readings`: Fetches recent sensor readings.
    -   **Query Parameters:**
        -   `limit` (int, optional, default=100): Maximum number of readings to return.
        -   `sensor_id` (str, optional): Filter readings by a specific sensor ID (e.g., `PHProbe-Tank1`).
        -   `type` (str, optional): Filter readings by sensor type (e.g., `pH`, `EC`).
    -   **Example:** `http://<pi_ip>:5000/readings?limit=50&type=pH`
    -   **Returns:** JSON array of reading objects, e.g., `[{"timestamp": "...", "sensor_id": "...", "type": "...", "value": ...}, ...]`.
-   `GET /status`: Simple health check endpoint.
    -   **Returns:** `{"status": "ok"}`

## Customization & Testing

-   **Arduino Data Format:** Adjust `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR` in `config.py` to match your Arduino's output.
-   **Sensor Model:** Extend `SensorReading` in `models.py` as needed.
-   **Database:** Schema is in `data_processor.py`/`database_setup.py`. Update both if you add columns.
-   **Manual Entry Options:** Update `PREDEFINED_SENSOR_TYPES` and `SENSOR_ID_MAP` in `manual_entry_gui.py` for your sensors.
-   **API:** Add endpoints to `api_server.py` as needed.
-   **Integration Testing:**
    - See `test_integration.py` for end-to-end and API tests. Run with:
      ```bash
      pytest test_integration.py
      ```
    - Tests use a temporary database and cover DB init, parsing, storage, and API endpoints.

## Additional Documentation
-   [`setup.md`](./setup.md): Full setup (Docker, Pi, WSL2, Windows, troubleshooting)
-   [`setup_appendix.md`](./setup_appendix.md): Windows/WSL2/usbipd/COM port bridging
-   `test_integration.py`: Integration tests for DB and API