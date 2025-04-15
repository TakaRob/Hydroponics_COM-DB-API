# Raspberry Pi Hydroponics Logger & API

This project runs entirely on a Raspberry Pi. It reads sensor data from an Arduino connected via serial port, processes the data into structured objects, timestamps it, stores it in a local SQLite database, and provides a REST API to query the stored data. A manual entry GUI is also included for backup/testing.

## For whomever puts this on the rasppi.
Steps:
1. Go through `config.py` and set up the serial port, database name, and API port. Ensure `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR` match your Arduino output exactly.
2. Install SQLite if not already present (`sudo apt-get update && sudo apt-get install sqlite3`).
3. Follow the Setup and Running instructions below.
4. To run the data logger and API server continuously in the background, consider using tools like `tmux`, `screen`, or setting up `systemd` services. I am trying to set up a docker image, but if that isn't set up it can be running in a terminal.

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

1.  **Clone the repository on your Raspberry Pi:**
    ```bash
    git clone https://github.com/TakaRob/HydroponicsRaspi-Api.git # Replace with your actual repo URL if different
    cd HydroponicsRaspi-Api
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # To deactivate later: deactivate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install SQLite (if not present):**
    ```bash
    sudo apt-get update
    sudo apt-get install sqlite3
    ```
5.  **Configure the application:**
    -   Edit `config.py`:
        -   **Set `SERIAL_PORT`** to the correct device path for your Arduino connection on the Pi (e.g., `/dev/ttyACM0`, `/dev/ttyUSB0`). Use `python -m serial.tools.list_ports -v` to help find it.
        -   Ensure `SERIAL_BAUD_RATE` matches the `Serial.begin()` rate in your Arduino code (e.g., `9600`).
        -   **CRITICAL:** Verify `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR` match *exactly* how your Arduino sends data. The default assumes `SensorID,SensorType,Value` sent on separate lines. The `ARDUINO_DATA_ORDER` list **must** contain the strings `"SensorID"`, `"SensorType"`, and `"Value"`.
        -   Adjust `DATABASE_NAME`, `API_HOST`, `API_PORT` if needed.
6.  **Set up the Arduino:**
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
7.  **Permissions (Linux/Pi):** You might need to add your user to the `dialout` group to access the serial port:
    ```bash
    sudo usermod -a -G dialout $USER
    ```
    You'll need to **log out and log back in** (or reboot) for this change to take effect.

## Running the Application (on the Pi)

You typically need two terminals/processes running in the background (e.g., using `tmux` or `screen`): one for the data logger and one for the API server.

1.  **Initialize the Database (Run once):**
    This ensures the database file and table schema are correctly set up.
    ```bash
    python database_setup.py
    ```
    *(Note: The logger and API server also attempt to initialize the DB if it doesn't exist, but running this script explicitly first is good practice).*

2.  **Run the Serial Data Logger:**
    This script listens to the Arduino, uses `data_processor` to parse the data into `SensorReading` objects, and stores them in the database.
    ```bash
    python serial_data_logger.py
    ```
    Press `Ctrl+C` to stop it gracefully. For continuous operation, run it in the background (e.g., `nohup python serial_data_logger.py &`) or use a terminal multiplexer (`tmux`, `screen`) or configure it as a `systemd` service. Check its log output for errors.

3.  **Run the API Server:**
    This script serves the REST API, allowing you to query the data stored by the logger.
    ```bash
    python api_server.py
    ```
    The API will be available at `http://<raspberry-pi-ip>:<API_PORT>` (e.g., `http://192.168.1.100:5000`). Run this in the background similarly to the logger.

4.  **Run the Manual Entry GUI (Optional, requires Desktop Environment):**
    If you need to manually add readings or test the database storage.
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

## Customization

-   **Arduino Data Format:** This is the most common customization. Carefully adjust `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR` in `config.py` to match your Arduino's `Serial.print`/`println` statements. Remember that the parser in `data_processor.py` relies on these settings.
-   **Sensor Model:** The `SensorReading` class in `models.py` can be extended. For example, you could add validation methods (e.g., check if a pH value is within 0-14) or methods for unit conversion.
-   **Database:** The schema is defined in `data_processor.py` (and mirrored in `database_setup.py`). You could add more columns if needed (e.g., location, batch ID). Remember to update the `SensorReading` class and database interaction code accordingly.
-   **Manual Entry Options:** Update `PREDEFINED_SENSOR_TYPES` and `SENSOR_ID_MAP` near the top of `manual_entry_gui.py` to reflect your specific sensors.
-   **API:** Add more complex query endpoints or data aggregation endpoints to `api_server.py`.