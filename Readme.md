# Raspberry Pi Hydroponics Logger & API

This project runs entirely on a Raspberry Pi. It reads sensor data from an Arduino connected via serial port, processes and timestamps the data, stores it in a local SQLite database, and provides a REST API to query the stored data. A manual entry GUI is also included for backup/testing.

## For whomever puts this on the rasppi. 
Steps: 
1. Go through Config.py and set up the port, db name, and api port.
2. 


## Architecture

Arduino (Sensors) --> Serial Port --> Raspberry Pi --> Python Script (`serial_data_logger.py`) --> SQLite DB (`sensor_data.db`) --> Flask API (`api_server.py`)

## Project Structure

- `config.py`: Configuration settings (Serial Port, Baud Rate, Database name, API port, etc.). **MODIFY THIS FIRST!**
- `requirements.txt`: Python dependencies (`Flask`, `pyserial`).
- `serial_reader.py`: Helper module for handling serial communication with the Arduino.
- `data_processor.py`: Parses serial data, adds timestamp, formats for DB, and handles DB interaction.
- `database_setup.py`: (Optional) Script to explicitly initialize the database schema.
- `api_server.py`: Runs a Flask-based REST API server (on the Pi) to query the database.
- `serial_data_logger.py`: Main script to continuously listen to serial port and store data. **RUN THIS FOR DATA COLLECTION.**
- `manual_entry_gui.py`: A GUI application (runnable on Pi desktop) for manually entering sensor data.
- `.gitignore`: Standard Git ignore file.
- `README.md`: This file.

## Setup

1.  **Clone the repository on your Raspberry Pi:**
    ```bash
    git clone https://github.com/TakaRob/HydroponicsRaspi-Api.git
    cd HydroponicsRaspi-Api
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure the application:**
    -   Edit `config.py`:
        -   **Set `SERIAL_PORT`** to the correct device path for your Arduino connection on the Pi (e.g., `/dev/ttyACM0`, `/dev/ttyUSB0`). You can use `python -m serial.tools.list_ports` to help find it.
        -   Ensure `SERIAL_BAUD_RATE` matches the `Serial.begin()` rate in your Arduino code (e.g., `9600`).
        -   Verify `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR` match how your Arduino sends data. The default assumes `"SensorID,SensorType,Value"`.
        -   Adjust `DATABASE_NAME`, `API_HOST`, `API_PORT` if needed.
5.  **Set up the Arduino:**
    -   Connect the Arduino to the Raspberry Pi via USB.
    -   Upload Arduino code that reads your sensors and prints the data to the Serial port in the format specified by `ARDUINO_DATA_ORDER` and `ARDUINO_DATA_SEPARATOR`, followed by a newline (`println`).
    -   *Example Arduino `loop()` snippet:*
        ```c++
        void loop() {
          // Read your sensors
          float pHValue = readPHSensor();
          float ECValue = readECSensor();
          float tempValue = readTempSensor();

          // Print each reading on a new line in the expected format
          Serial.print("PHProbe-Tank1,pH,");
          Serial.println(pHValue);

          Serial.print("ECMeter-Tank1,EC,");
          Serial.println(ECValue);

          Serial.print("TempProbe-Tank1,Water temperature,");
          Serial.println(tempValue);

          delay(5000); // Wait 5 seconds before sending next batch
        }
        ```
        *(Adjust Sensor IDs, types, and reading functions)*
6.  **Permissions (Linux/Pi):** You might need to add your user to the `dialout` group to access the serial port:
    ```bash
    sudo usermod -a -G dialout $USER
    ```
    You'll need to **log out and log back in** for this change to take effect.

## Running the Application (on the Pi)

You typically need two terminals/processes running in the background (or using `tmux`/`screen`): one for the data logger and one for the API server.

1.  **Initialize the Database (Run once):**
    ```bash
    python database_setup.py
    ```

2.  **Run the Serial Data Logger:**
    This script listens to the Arduino and saves data to the database.
    ```bash
    python serial_data_logger.py
    ```
    Press `Ctrl+C` to stop it gracefully. Run this in the background using `nohup` or a terminal multiplexer like `tmux` or `screen` for continuous operation.

3.  **Run the API Server:**
    This script serves the REST API from the Pi.
    ```bash
    python api_server.py
    ```
    The API will be available at `http://<raspberry-pi-ip>:<API_PORT>`. Run this in the background as well.

4.  **Run the Manual Entry GUI (Optional, requires Desktop Environment):**
    ```bash
    python manual_entry_gui.py
    ```

## API Endpoints

(Served from the Raspberry Pi)

-   `GET /readings`: Fetches sensor readings. Parameters: `limit`, `sensor_id`, `type`.
-   `GET /status`: Health check.

## Customization

-   **Arduino Data Format:** If your Arduino sends data differently, update `ARDUINO_DATA_ORDER`, `ARDUINO_DATA_SEPARATOR` in `config.py` and adjust the parsing logic in `data_processor.py:format_data_for_db`.
-   **Manual Entry Options:** Update `PREDEFINED_SENSOR_TYPES` and `SENSOR_ID_MAP` in `manual_entry_gui.py`.