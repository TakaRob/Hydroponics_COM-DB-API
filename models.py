# models.py
import datetime

class SensorReading:
    """
    Represents a single sensor reading with its metadata.
    """
    def __init__(self, sensor_id: str, sensor_type: str, value: float, timestamp: datetime.datetime = None):
        """
        Initializes a SensorReading instance.

        Args:
            sensor_id: The unique identifier of the sensor (e.g., "PHProbe-Tank1").
            sensor_type: The type of measurement (e.g., "pH", "EC").
            value: The numerical sensor reading.
            timestamp: The time the reading was taken/processed. Defaults to now (UTC).
        """
        if not isinstance(sensor_id, str) or not sensor_id:
            raise ValueError("sensor_id must be a non-empty string")
        if not isinstance(sensor_type, str) or not sensor_type:
            raise ValueError("sensor_type must be a non-empty string")
        try:
            self.value = float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"value must be convertible to float: {value}") from e

        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the reading."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "sensor_id": self.sensor_id,
            "type": self.sensor_type,
            "value": self.value
        }

    def to_db_tuple(self) -> tuple:
        """Returns a tuple formatted for database insertion."""
        # Ensure timestamp is timezone-naive if DB requires it, or formatted correctly.
        # Using ISO format string for SQLite compatibility and clarity.
        return (self.timestamp.isoformat(), self.sensor_id, self.sensor_type, self.value)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"SensorReading(id='{self.sensor_id}', type='{self.sensor_type}', "
                f"value={self.value}, time='{self.timestamp.isoformat()}')")

# Example of how you might define known sensor types (optional, but good practice)
# You could load this from config.py or define it here/elsewhere
# KNOWN_SENSOR_TYPES = {
#     "pH": {"unit": "pH", "description": "Acidity/Alkalinity", "min_val": 0, "max_val": 14},
#     "EC": {"unit": "mS/cm", "description": "Electrical Conductivity", "min_val": 0},
#     "Water temperature": {"unit": "°C", "description": "Water Temperature"},
#     # Add more definitions as needed
# }

# You could add methods to SensorReading to validate against KNOWN_SENSOR_TYPES if desired
# def is_valid(self):
#     if self.sensor_type in KNOWN_SENSOR_TYPES:
#         rules = KNOWN_SENSOR_TYPES[self.sensor_type]
#         if "min_val" in rules and self.value < rules["min_val"]:
#             return False
#         if "max_val" in rules and self.value > rules["max_val"]:
#             return False
#     # Add more validation if needed
#     return True