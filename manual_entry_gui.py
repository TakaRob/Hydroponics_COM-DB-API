# manual_entry_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone
import logging

# Assuming data_processor handles database interactions now using SensorReading
import data_processor
from models import SensorReading # Import the class
import config # To potentially get default/known values if defined there

# --- Configuration (Can be moved to config.py or kept simple here) ---
# Example predefined values - customize as needed
# Ideally, load these from a central config or the KNOWN_SENSOR_TYPES in models.py
PREDEFINED_SENSOR_TYPES = ["pH", "EC", "Water temperature", "Air temperature", "Humidity"]
# Example Sensor IDs - customize or use dynamic entry
SENSOR_ID_MAP = {
    "Tank 1 pH Probe": "PHProbe-Tank1",
    "Tank 1 EC Meter": "ECMeter-Tank1",
    "Tank 1 Water Temp": "TempProbe-Tank1",
    "Grow Tent Air Temp": "AirTemp-Tent1",
    "Grow Tent Humidity": "Humidity-Tent1",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ManualEntryApp:
    def __init__(self, root):
        self.root = root
        root.title("Manual Sensor Entry")

        # Frame for input fields
        input_frame = ttk.Frame(root, padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Sensor ID Selection
        ttk.Label(input_frame, text="Sensor ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sensor_id_var = tk.StringVar()
        # Use display names as keys, store actual IDs as values
        self.sensor_id_combobox = ttk.Combobox(input_frame, textvariable=self.sensor_id_var,
                                               values=list(SENSOR_ID_MAP.keys()), width=30)
        self.sensor_id_combobox.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        # Optional: Allow free text entry too?
        # self.sensor_id_entry = ttk.Entry(input_frame, textvariable=self.sensor_id_var, width=30)
        # self.sensor_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        # Sensor Type Selection
        ttk.Label(input_frame, text="Sensor Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sensor_type_var = tk.StringVar()
        self.sensor_type_combobox = ttk.Combobox(input_frame, textvariable=self.sensor_type_var,
                                                 values=PREDEFINED_SENSOR_TYPES, width=30)
        self.sensor_type_combobox.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        # Optional: Free text entry
        # self.sensor_type_entry = ttk.Entry(input_frame, textvariable=self.sensor_type_var, width=30)
        # self.sensor_type_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        # Value Entry
        ttk.Label(input_frame, text="Value:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(input_frame, textvariable=self.value_var, width=30)
        self.value_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        # Submit Button
        self.submit_button = ttk.Button(input_frame, text="Submit Reading", command=self.submit_reading)
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Status Label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(input_frame, textvariable=self.status_var, foreground="green")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

        # Set focus
        self.sensor_id_combobox.focus()
        # Make columns resizable
        input_frame.columnconfigure(1, weight=1)

    def submit_reading(self):
        # Get values from the GUI
        display_name = self.sensor_id_var.get()
        sensor_id = SENSOR_ID_MAP.get(display_name, display_name) # Get ID from map, or use input if not found
        sensor_type = self.sensor_type_var.get()
        value_str = self.value_var.get()

        # Basic Validation
        if not sensor_id or not sensor_type or not value_str:
            messagebox.showerror("Input Error", "All fields are required.")
            self.set_status("Error: All fields required.", "red")
            return

        try:
            # Create a SensorReading object (this handles value conversion)
            # Use current UTC time for manual entries
            timestamp = datetime.now(timezone.utc)
            reading = SensorReading(sensor_id=sensor_id,
                                    sensor_type=sensor_type,
                                    value=value_str, # SensorReading constructor handles float conversion
                                    timestamp=timestamp)

            # Store the reading using the data_processor
            success = data_processor.store_reading(reading)

            if success:
                messagebox.showinfo("Success", f"Reading submitted successfully:\n{reading}")
                self.set_status("Reading submitted successfully.", "green")
                # Clear fields after successful submission
                # self.sensor_id_var.set('') # Keep selected ID?
                # self.sensor_type_var.set('') # Keep selected type?
                self.value_var.set('')
                self.value_entry.focus() # Set focus back to value for next entry
            else:
                messagebox.showerror("Database Error", "Failed to store the reading in the database. Check logs.")
                self.set_status("Error: Failed to store reading.", "red")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            self.set_status(f"Error: {e}", "red")
        except Exception as e:
            logging.exception("Error during manual submission") # Log full traceback
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.set_status(f"Unexpected error: {e}", "red")

    def set_status(self, message, color):
        self.status_var.set(message)
        self.status_label.config(foreground=color)
        # Clear status after a few seconds
        self.root.after(5000, lambda: self.status_var.set(""))


if __name__ == "__main__":
    # Ensure database exists before starting GUI
    try:
        data_processor.initialize_database()
    except Exception as e:
         logging.error(f"Failed to initialize database before starting GUI: {e}")
         # Show error popup if GUI is the primary interaction
         # messagebox.showerror("Startup Error", f"Could not initialize database: {e}")
         # sys.exit(1) # Or allow GUI to start but show persistent error?

    root = tk.Tk()
    app = ManualEntryApp(root)
    root.mainloop()