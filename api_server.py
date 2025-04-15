# api_server.py
from flask import Flask, jsonify, request
import logging

import config
import data_processor # Uses the updated data_processor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

@app.route('/readings', methods=['GET'])
def get_readings():
    """
    API endpoint to fetch sensor readings.
    Query Parameters:
        limit (int): Max number of readings (default 100).
        sensor_id (str): Filter by sensor ID.
        type (str): Filter by sensor type.
    """
    try:
        limit = request.args.get('limit', default=100, type=int)
        sensor_id = request.args.get('sensor_id', default=None, type=str)
        # Use 'type' as query param name to match DB column
        sensor_type = request.args.get('type', default=None, type=str)

        # Ensure limit is reasonable
        limit = max(1, min(limit, 1000)) # Example: Clamp limit between 1 and 1000

        readings = data_processor.get_readings_from_db(limit=limit, sensor_id=sensor_id, sensor_type=sensor_type)

        # data_processor.get_readings_from_db already returns a list of dicts
        return jsonify(readings)

    except Exception as e:
        logging.error(f"Error in /readings endpoint: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Health check endpoint."""
    # Could add more checks here (e.g., database connectivity)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    logging.info(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    # Make sure database is initialized before starting server
    try:
        data_processor.initialize_database()
    except Exception as e:
        logging.error(f"Failed to initialize database before starting API server: {e}")
        # Decide if you want to exit or proceed
        # sys.exit(1)

    app.run(host=config.API_HOST, port=config.API_PORT, debug=False) # debug=False for production/background use