import pandas as pd
import sqlite3
import os
import math
from datetime import datetime

DB_FILE = "buses.db"
EXCEL_FILE = "__pycache__/bus_dataset.xlsx"

def init_db(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number   TEXT UNIQUE NOT NULL,
            bus_name       TEXT NOT NULL,
            route          TEXT,
            driver_name    TEXT NOT NULL,
            driver_contact TEXT,
            registered_on  TEXT
        )
    """)
    conn.commit()

def import_excel():
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: Could not find Excel file at {EXCEL_FILE}")
        return

    print(f"Reading {EXCEL_FILE}...")
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Check columns
    # We expect something like: Plate Number, Bus Name, Route, Driver Name, Driver Contact
    # Let's map them if they exist or try to guess.
    expected_cols = ["plate", "Plate", "Plate Number", "plate_number", 
                     "bus_name", "Bus Name", "Bus", "Route", "route",
                     "driver", "Driver", "Driver Name", "driver_name", 
                     "contact", "Contact", "Driver Contact", "driver_contact"]
    
    print("Columns found in Excel:", df.columns.tolist())
    
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)
    cur = conn.cursor()
    
    success_count = 0
    skip_count = 0

    for index, row in df.iterrows():
        # Heuristics to find columns
        plate = None
        bus_name = "Unknown Bus"
        route = "Unknown Route"
        driver = "Unknown Driver"
        contact = "N/A"

        for col in df.columns:
            col_lower = str(col).lower().strip()
            val = str(row[col]) if pd.notna(row[col]) else ""
            if not val:
                continue

            if "plate" in col_lower or "number" in col_lower:
                plate = val.upper().replace(" ", "").replace("-", "")
            elif "bus" in col_lower or "name" == col_lower:
                bus_name = val
            elif "route" in col_lower:
                route = val
            elif "driver" in col_lower and "contact" not in col_lower:
                driver = val
            elif "contact" in col_lower or "phone" in col_lower:
                contact = val

        if not plate:
            print(f"Skipping row {index+2}: No plate number found.")
            skip_count += 1
            continue

        try:
            cur.execute("""
                INSERT INTO buses (plate_number, bus_name, route, driver_name, driver_contact, registered_on)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (plate, bus_name, route, driver, contact, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            success_count += 1
        except sqlite3.IntegrityError:
            print(f"Skipping plate '{plate}': Already exists in database.")
            skip_count += 1
            
    conn.commit()
    conn.close()
    
    print(f"\nImport Complete:")
    print(f"  Successfully imported: {success_count}")
    print(f"  Skipped (duplicates or missing plate): {skip_count}")

if __name__ == "__main__":
    import_excel()
