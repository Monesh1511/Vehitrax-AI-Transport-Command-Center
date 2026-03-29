"""
Manual Bus Dataset Creator
Saves bus info to:
  1. buses.json  (easy to read/edit)
  2. buses.db    (SQLite database the main app uses)
"""

import json, sqlite3, os
from datetime import datetime

DB_FILE   = "buses.db"
JSON_FILE = "buses.json"

# ── Create SQLite database and tables ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number    TEXT NOT NULL,
            scheduled_entry TEXT NOT NULL,
            scheduled_exit  TEXT,
            day_of_week     TEXT,
            FOREIGN KEY (plate_number) REFERENCES buses(plate_number)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bus_events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            event_type   TEXT NOT NULL,
            timestamp    TEXT NOT NULL,
            confidence   REAL,
            camera_id    TEXT DEFAULT 'cam_01'
        )
    """)

    conn.commit()
    return conn


def add_bus(conn, data):
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO buses (plate_number, bus_name, route, driver_name, driver_contact, registered_on)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["plate_number"].upper().replace(" ", ""),
            data["bus_name"],
            data["route"],
            data["driver_name"],
            data["driver_contact"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        print(f"  ✓ Bus '{data['plate_number']}' added to database!")
        return True
    except sqlite3.IntegrityError:
        print(f"  ✗ Plate '{data['plate_number']}' already exists. Skipping.")
        return False


def add_schedule(conn, plate, entry_time, exit_time, day):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO schedules (plate_number, scheduled_entry, scheduled_exit, day_of_week)
        VALUES (?, ?, ?, ?)
    """, (plate.upper(), entry_time, exit_time, day.upper()))
    conn.commit()


def save_json(all_buses):
    with open(JSON_FILE, "w") as f:
        json.dump(all_buses, f, indent=2)
    print(f"\n  ✓ Also saved to {JSON_FILE}")


def view_all_buses(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM buses")
    rows = cur.fetchall()
    if not rows:
        print("\n  No buses in database yet.")
        return
    print("\n" + "="*70)
    print(f"{'ID':<4} {'Plate':<14} {'Bus Name':<16} {'Route':<12} {'Driver':<16} {'Contact'}")
    print("="*70)
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<14} {row[2]:<16} {row[3]:<12} {row[4]:<16} {row[5]}")
    print("="*70)
    print(f"Total: {len(rows)} bus(es)")


def main():
    print("\n" + "="*60)
    print("   BUS DATASET CREATOR")
    print("   Creates your manual bus registry database")
    print("="*60)

    conn      = init_db()
    all_buses = []

    # Load existing JSON if it exists
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE) as f:
            all_buses = json.load(f)
        print(f"\nLoaded {len(all_buses)} existing bus(es) from {JSON_FILE}")

    while True:
        print("\n--- MENU ---")
        print("1. Add new bus")
        print("2. View all buses")
        print("3. Add schedule for a bus")
        print("4. Exit")
        choice = input("\nChoose (1/2/3/4): ").strip()

        if choice == "1":
            print("\n-- Enter Bus Details --")
            plate   = input("Plate Number (e.g. TN01AB1234): ").strip().upper()
            name    = input("Bus Name (e.g. Express-7):       ").strip()
            route   = input("Route (e.g. Zone-A to Campus):   ").strip()
            driver  = input("Driver Name:                     ").strip()
            contact = input("Driver Contact (phone):          ").strip()

            data = {
                "plate_number":   plate,
                "bus_name":       name,
                "route":          route,
                "driver_name":    driver,
                "driver_contact": contact
            }

            if add_bus(conn, data):
                all_buses.append(data)
                save_json(all_buses)

        elif choice == "2":
            view_all_buses(conn)

        elif choice == "3":
            plate = input("Enter plate number: ").strip().upper()
            entry = input("Scheduled entry time (HH:MM, e.g. 08:30): ").strip()
            exit_ = input("Scheduled exit time  (HH:MM, e.g. 17:00): ").strip()
            day   = input("Day of week (MON/TUE/WED/THU/FRI/SAT/SUN or ALL): ").strip()

            if day.upper() == "ALL":
                for d in ["MON","TUE","WED","THU","FRI","SAT","SUN"]:
                    add_schedule(conn, plate, entry, exit_, d)
                print(f"  ✓ Schedule added for all days!")
            else:
                add_schedule(conn, plate, entry, exit_, day)
                print(f"  ✓ Schedule added for {day}!")

        elif choice == "4":
            print("\nDataset saved. You can now run the main pipeline.")
            break
        else:
            print("Invalid choice. Try again.")

    conn.close()


if __name__ == "__main__":
    main()
