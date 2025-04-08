# api_server.py

from flask import Flask, jsonify, request
import sqlite3
import logging
from config import DATABASE_NAME, TABLE_NAME, API_HOST, API_PORT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def get_db_connection():
    """Helper function to get DB connection for API requests."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

@app.route('/readings', methods=['GET'])
def get_readings():
    """
    API endpoint to fetch sensor readings.
    Supports filtering by sensor_id, sensor_type and limiting results.
    Example: /readings?limit=10&sensor_id=DHT22-1&type=temperature
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query
    query = f"SELECT * FROM {TABLE_NAME}"
    filters = []
    params = {}

    # Query parameters for filtering
    limit = request.args.get('limit', default=100, type=int) # Default limit 100
    sensor_id = request.args.get('sensor_id')
    sensor_type = request.args.get('type') # use 'type' for brevity in URL

    if sensor_id:
        filters.append("sensor_id = :sensor_id")
        params['sensor_id'] = sensor_id

    if sensor_type:
        filters.append("sensor_type = :sensor_type")
        params['sensor_type'] = sensor_type

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY timestamp DESC LIMIT :limit"
    params['limit'] = limit

    try:
        cursor.execute(query, params)
        readings = cursor.fetchall()
        conn.close()
        # Convert Row objects to dictionaries for JSON serialization
        result = [dict(row) for row in readings]
        return jsonify(result)

    except sqlite3.Error as e:
        logging.error(f"API database query error: {e}")
        conn.close()
        return jsonify({"error": "Database query failed"}), 500
    except Exception as e:
         logging.error(f"API unexpected error: {e}")
         if conn: conn.close()
         return jsonify({"error": "An internal server error occurred"}), 500


@app.route('/status', methods=['GET'])
def status():
    """Simple health check endpoint."""
    return jsonify({"status": "API is running"})

if __name__ == '__main__':
    logging.info(f"Starting Flask API server on http://{API_HOST}:{API_PORT}")
    # Set debug=False for production environments
    app.run(host=API_HOST, port=API_PORT, debug=True)