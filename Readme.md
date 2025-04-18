# Raspberry Pi Hydroponics Logger & API

This project runs entirely on a Raspberry Pi. It reads sensor data from an Arduino connected via serial port, processes the data into structured objects, timestamps it, stores it in a local SQLite database, and provides a REST API to query the stored data. A manual entry GUI is also included for backup/testing.

## For whomever puts this on the rasppi.
Steps:
1. Go through `config.py` and set up the serial port, database name, and API port. Ensure `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR` match your Arduino output exactly.
2. Install SQLite if not already present (`sudo apt-get update && sudo apt-get install sqlite3`).
3. Follow the Setup and Running instructions below.
4. To run the data logger and API server continuously in the background, consider using tools like `tmux`, `screen`, or setting up `systemd` services. **Docker deployment is now supported and recommended for both Raspberry Pi and development environments.** See the new setup instructions below for details. If Docker is not set up, you can still run the scripts in a terminal as before.

## Architecture

Arduino (Sensors) --> Serial Port --> Raspberry Pi --> Python Script (`serial_data_logger.py`) --> Data Processing (`data_processor.py` using `models.SensorReading`) --> SQLite DB (`sensor_data.db`) --> Flask API (`api_server.py`)

## Project Structure

-   `config.py`: Configuration settings (Serial Port, Baud Rate, Database name, API port, Arduino data format). **MODIFY THIS FIRST!**
-   `requirements.txt`: Python dependencies (`Flask`, `pyserial`).
-   `models.py`: Defines data structures, primarily the `SensorReading` class which represents a single, structured sensor measurement.
-   `serial_reader.py`: Helper module for handling serial communication with the Arduino.
-   `data_processor.py`: Parses raw serial data into `SensorReading` objects, handles database interactions (storage and retrieval).
-   `database_setup.py`: (Optional but Recommended) Script to explicitly initialize the database schema. Can be run once initially.
-   `api_server.py`: Runs a Flask-based REST API server (on the Pi) to query the database.
-   `serial_data_logger.py`: Main script to continuously listen to the serial port, process data using `data_processor`, and store it via `data_processor`. **RUN THIS FOR DATA COLLECTION.**
-   `manual_entry_gui.py`: A GUI application (runnable on Pi desktop) for manually entering sensor data (creates `SensorReading` objects).
-   `.gitignore`: Standard Git ignore file.
-   `README.md`: This file.

## Setup

**For all deployment and development environments, see the detailed setup guides:**
- [`setup.md`](./setup.md) — Covers Docker deployment (multi-arch), Raspberry Pi setup, and Windows/WSL2/usbipd integration for Arduino serial.
- [`setup_appendix.md`](./setup_appendix.md) — Step-by-step for bridging Windows COM ports to WSL/Ubuntu for Arduino serial access.

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
    - Edit `config.py` as before for serial port, baud rate, and Arduino data format.
    - See `setup.md` for device/port details on Pi and WSL2/Windows.
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
    You'll need to **log out and log back in** (or reboot) for this change to take effect.

## Running the Application

### Docker (Recommended)
See [`setup.md`](./setup.md) for full Docker usage. Typical commands:
```bash
docker pull takajirobson/rasppardapi:latest
docker run --rm -it --device=/dev/ttyACM0 --env SERIAL_PORT=/dev/ttyACM0 -p 5000:5000 takajirobson/rasppardapi:latest
```
- For Windows/WSL2/usbipd, see [`setup_appendix.md`](./setup_appendix.md) for how to bridge the Arduino serial port.

### Manual Python (Legacy)
You typically need two terminals/processes running in the background (e.g., using `tmux` or `screen`): one for the data logger and one for the API server.

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

(Served from the Raspberry Pi at `http://<raspberry-pi-ip>:<API_PORT>`)

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