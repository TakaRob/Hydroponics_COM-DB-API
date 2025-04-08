# manual_entry_gui.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import logging
import json

# *** Use format from config for consistency ***
from config import MANUAL_ENTRY_TIMESTAMP_FORMAT
import data_processor # To use insertion logic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration --- (Sensor types/map need updating if desired, but logic is same)
PREDEFINED_SENSOR_TYPES = [
    "pH", "EC", "Water level", "Water temperature", "ORP", "other",
]
SENSOR_ID_MAP = { # Keep this relevant for manual input options
    "pH": ["PHProbe-Tank1", "PHProbe-Reservoir", "Manual-pH"],
    "EC": ["ECMeter-Tank1", "ECMeter-Reservoir", "Manual-EC"],
    "Water level": ["Ultrasonic-Tank1", "FloatSwitch-Safety", "Manual-Level"],
    "Water temperature": ["TempProbe-Tank1-Submerged", "TempProbe-Reservoir", "Manual-Temp"],
    "ORP": ["ORPMeter-Tank1", "ORPMeter-Reservoir", "Manual-ORP"],
    "other": ["ManualInput-Backup", "TestSensor-007"]
}
for sensor_type in PREDEFINED_SENSOR_TYPES:
    if sensor_type not in SENSOR_ID_MAP:
        SENSOR_ID_MAP[sensor_type] = [f"Generic-{sensor_type.replace(' ','')}-Sensor"]

TIMESTAMP_FORMAT = MANUAL_ENTRY_TIMESTAMP_FORMAT # Use config value

# --- GUI Application Class --- (Most code remains the same)
class ManualEntryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Manual Sensor Data Entry")
        style = ttk.Style()
        style.theme_use('clam')

        self.sensor_type = tk.StringVar()
        self.selected_sensor_id = tk.StringVar()
        self.value = tk.StringVar()
        self.timestamp_str = tk.StringVar()

        # --- UI Elements setup (same as before) ---
        frame = ttk.Frame(root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Type Dropdown (Row 0)
        ttk.Label(frame, text="Sensor Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        # ... (rest of Type setup)
        self.type_combobox = ttk.Combobox(frame, textvariable=self.sensor_type, values=PREDEFINED_SENSOR_TYPES, width=27, state='readonly')
        self.type_combobox.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        self.type_combobox.current(0)
        self.type_combobox.bind("<<ComboboxSelected>>", self.update_sensor_ids)

        # ID Dropdown (Row 1)
        ttk.Label(frame, text="Sensor ID:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        # ... (rest of ID setup)
        self.id_combobox = ttk.Combobox(frame, textvariable=self.selected_sensor_id, width=27, state='readonly')
        self.id_combobox.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

        # Value Entry (Row 2)
        ttk.Label(frame, text="Value:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        # ... (rest of Value setup)
        self.value_entry = ttk.Entry(frame, textvariable=self.value, width=30)
        self.value_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

        # Timestamp Entry & Button (Row 3)
        ttk.Label(frame, text="Timestamp:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.ts_entry = ttk.Entry(frame, textvariable=self.timestamp_str, width=20)
        self.ts_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        self.set_now_button = ttk.Button(frame, text="Now", command=self.set_timestamp_now)
        self.set_now_button.grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        self.set_timestamp_now() # Uses TIMESTAMP_FORMAT

        # Submit Button (Row 4)
        self.submit_button = ttk.Button(frame, text="Submit Data", command=self.submit_data)
        self.submit_button.grid(row=4, column=0, columnspan=3, padx=5, pady=15)

        # Status Label (Row 5)
        self.status_label = ttk.Label(frame, text="", foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

        frame.columnconfigure(1, weight=1)
        self.update_sensor_ids() # Initial population

    def update_sensor_ids(self, event=None):
        # Unchanged
        selected_type = self.sensor_type.get()
        ids_for_type = SENSOR_ID_MAP.get(selected_type, [])
        if ids_for_type:
            self.id_combobox['values'] = ids_for_type
            self.id_combobox.current(0); self.id_combobox.config(state='readonly')
        else:
            self.id_combobox['values'] = []; self.selected_sensor_id.set('')
            self.id_combobox.config(state='disabled')
        logging.debug(f"Type changed to '{selected_type}'. Updated IDs: {ids_for_type}")

    def set_timestamp_now(self):
        """Sets timestamp entry to now using configured format."""
        now_str = datetime.now().strftime(TIMESTAMP_FORMAT)
        self.timestamp_str.set(now_str)

    def submit_data(self):
        """Validates input and submits data to the database."""
        # Get values - unchanged
        s_type = self.sensor_type.get(); s_id = self.selected_sensor_id.get()
        s_value_str = self.value.get().strip()
        s_timestamp_str = self.timestamp_str.get().strip()

        # Validation - unchanged, uses TIMESTAMP_FORMAT from config in error message
        if not s_id and self.id_combobox['state'] != 'disabled':
             messagebox.showerror("Error", "Select Sensor ID."); return
        # ... (rest of validation)
        if not all([s_type, s_value_str, s_timestamp_str]):
            messagebox.showerror("Error", "Type, Value, Timestamp required."); return
        try: s_value_float = float(s_value_str)
        except ValueError: messagebox.showerror("Error", "Value must be number."); return
        try: dt_object = datetime.strptime(s_timestamp_str, TIMESTAMP_FORMAT)
        except ValueError:
             err_msg = f"Invalid Timestamp format. Use '{TIMESTAMP_FORMAT}'"
             messagebox.showerror("Error", err_msg); return

        # Prepare data for insertion - unchanged structure
        manual_data_dict = {"sensor_id": s_id, "sensor_type": s_type, "value": s_value_float, "manual_ts": s_timestamp_str}
        record_to_insert = {
            "timestamp": dt_object, "sensor_id": s_id, "sensor_type": s_type,
            "value": s_value_float, "raw_data": json.dumps(manual_data_dict)
        }

        # Insert - unchanged call
        success = data_processor.insert_data_to_db([record_to_insert])
        if success:
            self.status_label.config(text="Data submitted!", foreground="green")
            messagebox.showinfo("Success", "Data submitted.")
        else:
            self.status_label.config(text="DB Error.", foreground="red")
            messagebox.showerror("DB Error", "Could not write to DB.")

# --- Main Execution --- (Unchanged)
if __name__ == "__main__":
    logging.info("Checking database table...")
    if not data_processor.create_table_if_not_exists():
        logging.error("DB table could not be verified/created.")
        if not messagebox.askretrycancel("DB Error", "Could not init DB. Continue?"): exit()
    logging.info("Launching Manual Entry GUI...")
    main_window = tk.Tk(); app = ManualEntryApp(main_window)
    main_window.mainloop()
    logging.info("Manual Entry GUI closed.")