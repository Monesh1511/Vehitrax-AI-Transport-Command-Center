"""
Complete Bus Tracking Pipeline
- Opens camera
- Detects buses with YOLO
- Reads number plate with EasyOCR
- Looks up plate in your dataset (buses.db)
- Records entry/exit with timestamp
- Shows everything on screen
"""

import cv2, sqlite3, re, time, json, requests
from ultralytics import YOLO
from datetime import datetime
from collections import defaultdict
from ocr import extract_text_with_conf

# ── Config ────────────────────────────────────────────────────────────────────
CAMERA_INDEX  = 0          # change to 1 or 2 if camera doesn't open
DB_FILE       = "buses.db"
ENTRY_LINE_Y  = None       # set automatically to 40% of frame height
EXIT_LINE_Y   = None       # set automatically to 60% of frame height
COOLDOWN_SEC  = 30         # seconds before same plate can trigger again
CONF_THRESHOLD= 0.4
SHOW_CAMERA_TEXT_OVERLAY = False  # Keep terminal logs, hide in-frame text panels/labels

# ── Load Models ───────────────────────────────────────────────────────────────
print("[1/3] Loading YOLO model...")
model  = YOLO("yolo11n.pt")   # auto-downloads if not present
print("[2/3] Loading OCR model (EasyOCR)...")
print("[3/3] Connecting to database...")
conn   = sqlite3.connect(DB_FILE)
conn.executescript("""
    CREATE TABLE IF NOT EXISTS buses (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number   TEXT UNIQUE NOT NULL,
        bus_name       TEXT NOT NULL,
        route          TEXT,
        driver_name    TEXT NOT NULL,
        driver_contact TEXT,
        registered_on  TEXT
    );
    CREATE TABLE IF NOT EXISTS schedules (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number    TEXT NOT NULL,
        scheduled_entry TEXT NOT NULL,
        scheduled_exit  TEXT,
        day_of_week     TEXT,
        FOREIGN KEY (plate_number) REFERENCES buses(plate_number)
    );
    CREATE TABLE IF NOT EXISTS bus_events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL,
        event_type   TEXT NOT NULL,
        timestamp    TEXT NOT NULL,
        confidence   REAL,
        camera_id    TEXT DEFAULT 'cam_01'
    );
""")
print("All systems ready!\n")

# ── Database helpers ──────────────────────────────────────────────────────────
PLATE_REGEX = re.compile(r'[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}')

def lookup_bus(plate: str) -> dict | None:
    cur = conn.cursor()
    cur.execute("SELECT * FROM buses WHERE plate_number=?", (plate,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0], "plate": row[1], "bus_name": row[2],
        "route": row[3], "driver": row[4], "contact": row[5]
    }

def get_schedule(plate: str, day: str) -> dict | None:
    cur = conn.cursor()
    cur.execute("""
        SELECT scheduled_entry, scheduled_exit FROM schedules
        WHERE plate_number=? AND (day_of_week=? OR day_of_week='ALL')
    """, (plate, day))
    row = cur.fetchone()
    return {"entry": row[0], "exit": row[1]} if row else None

def record_event(plate: str, event_type: str, confidence: float, bus_info: dict = None):
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bus_events (plate_number, event_type, timestamp, confidence)
        VALUES (?, ?, ?, ?)
    """, (plate, event_type, timestamp_str, confidence))
    conn.commit()

    # Send event to backend dashboard
    try:
        payload = {
            "plate_number": plate,
            "camera_id": "camera_01",
            "timestamp": now.isoformat(),
            "confidence": float(confidence),
            "bus_name": bus_info["bus_name"] if bus_info else "UNKNOWN",
            "driver_name": bus_info["driver"] if bus_info else "UNKNOWN",
            "route": bus_info["route"] if bus_info else "UNKNOWN"
        }
        requests.post("http://127.0.0.1:8000/api/events/detection", json=payload, timeout=2)
    except Exception as e:
        print(f"Failed to send event to backend: {e}")

def get_today_events():
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        SELECT plate_number, event_type, timestamp FROM bus_events
        WHERE timestamp LIKE ? ORDER BY timestamp DESC LIMIT 10
    """, (f"{today}%",))
    return cur.fetchall()

def compute_score(actual_time_str: str, scheduled_time_str: str) -> int:
    fmt = "%H:%M"
    actual    = datetime.strptime(actual_time_str[:5],    fmt)
    scheduled = datetime.strptime(scheduled_time_str[:5], fmt)
    diff_min  = (actual - scheduled).total_seconds() / 60
    if diff_min <= 0:     return 100
    elif diff_min <= 5:   return 90
    elif diff_min <= 10:  return 75
    elif diff_min <= 20:  return 55
    else:                 return max(0, int(40 - diff_min))

# ── OCR helpers ───────────────────────────────────────────────────────────────
def read_plate(crop) -> tuple[str, float]:
    if crop is None or crop.size == 0:
        return "", 0.0
    text, conf, engine = extract_text_with_conf(crop)
    if not text:
        return "", 0.0
    m = PLATE_REGEX.search(text)
    plate = m.group(0) if m else text
    if engine:
        print(f"[OCR] engine={engine} plate={plate} conf={conf:.2f}")
    return plate, conf

# ── State tracking ─────────────────────────────────────────────────────────────
bus_state   = defaultdict(lambda: "outside")  # plate -> inside/outside
last_event  = {}                              # plate -> timestamp
event_log   = []                              # recent events for display

def process_bus(frame, bbox, frame_h):
    global ENTRY_LINE_Y, EXIT_LINE_Y
    if ENTRY_LINE_Y is None:
        ENTRY_LINE_Y = int(frame_h * 0.45)
        EXIT_LINE_Y  = int(frame_h * 0.55)

    x1, y1, x2, y2 = map(int, bbox)
    cy = (y1 + y2) // 2

    # Crop bus region and read plate
    bus_crop   = frame[y1:y2, x1:x2]
    plate, conf = read_plate(bus_crop)

    if not plate or len(plate) < 6:
        return None  # not a readable plate

    # Cooldown check
    now = time.time()
    if now - last_event.get(plate, 0) < COOLDOWN_SEC:
        return plate  # still in cooldown

    # Event detection via virtual line crossing
    state = bus_state[plate]
    event = None

    if cy > ENTRY_LINE_Y and state == "outside":
        bus_state[plate] = "inside"
        last_event[plate] = now
        event = "ENTRY"

    elif cy < EXIT_LINE_Y and state == "inside":
        bus_state[plate] = "outside"
        last_event[plate] = now
        event = "EXIT"

    if event:
        # Look up in database
        bus_info = lookup_bus(plate)
        day      = datetime.now().strftime("%a").upper()[:3]
        schedule = get_schedule(plate, day) if bus_info else None
        score    = None
        if schedule and event == "ENTRY":
            current_time = datetime.now().strftime("%H:%M")
            score = compute_score(current_time, schedule["entry"])

        record_event(plate, event, conf, bus_info)

        log_entry = {
            "plate":    plate,
            "event":    event,
            "time":     datetime.now().strftime("%H:%M:%S"),
            "bus_name": bus_info["bus_name"] if bus_info else "UNKNOWN",
            "driver":   bus_info["driver"]   if bus_info else "UNKNOWN",
            "score":    score,
            "conf":     conf
        }
        event_log.insert(0, log_entry)
        if len(event_log) > 8:
            event_log.pop()

        print(f"\n{'='*50}")
        print(f"  {event}: {plate}")
        if bus_info:
            print(f"  Bus:    {bus_info['bus_name']}")
            print(f"  Driver: {bus_info['driver']}  ({bus_info['contact']})")
            print(f"  Route:  {bus_info['route']}")
        else:
            print("  ⚠ UNREGISTERED BUS")
        if score is not None:
            print(f"  Score:  {score}/100")
        print(f"{'='*50}")

    return plate

# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_ui(frame, detections):
    h, w = frame.shape[:2]

    # Entry/exit lines
    cv2.line(frame, (0, ENTRY_LINE_Y), (w, ENTRY_LINE_Y), (0, 255, 0), 2)
    cv2.putText(frame, "ENTRY LINE", (10, ENTRY_LINE_Y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.line(frame, (0, EXIT_LINE_Y), (w, EXIT_LINE_Y), (0, 0, 255), 2)
    cv2.putText(frame, "EXIT LINE",  (10, EXIT_LINE_Y  + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Event log panel (right side)
    panel_x = w - 320
    cv2.rectangle(frame, (panel_x, 0), (w, min(h, 40 + 60 * len(event_log))),
                  (0, 0, 0), -1)
    cv2.putText(frame, "RECENT EVENTS", (panel_x + 5, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    for i, ev in enumerate(event_log):
        y      = 50 + i * 60
        color  = (0, 255, 80) if ev["event"] == "ENTRY" else (80, 80, 255)
        cv2.putText(frame, f"{ev['event']} {ev['plate']}", (panel_x + 5, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.putText(frame, f"{ev['bus_name']} | {ev['time']}", (panel_x + 5, y + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
        if ev["score"] is not None:
            sc_col = (0,200,0) if ev["score"]>=80 else (0,165,255) if ev["score"]>=60 else (0,0,200)
            cv2.putText(frame, f"Score: {ev['score']}/100", (panel_x + 5, y + 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, sc_col, 1)

    # Stats bar at bottom
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT COUNT(*) FROM bus_events WHERE timestamp LIKE ? AND event_type='entry'", (f"{today}%",))
    entries = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bus_events WHERE timestamp LIKE ? AND event_type='exit'", (f"{today}%",))
    exits = cur.fetchone()[0]

    cv2.rectangle(frame, (0, h-40), (w, h), (30, 30, 30), -1)
    cv2.putText(frame, f"Today:  Entries={entries}  Exits={exits}  Inside={max(0,entries-exits)}  |  Press Q to quit",
                (10, h-12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize latency
    
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera {CAMERA_INDEX}")
        print("Try changing CAMERA_INDEX to 1 or 2 at the top of this file")
        return

    print("Camera opened. Detection running. Press Q to quit.\n")
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Lost camera feed.")
            break

        frame_count += 1
        # Run YOLO every 3rd frame to save CPU
        if frame_count % 3 == 0:
            results = model(frame, conf=CONF_THRESHOLD, verbose=False)
            found_vehicle = False

            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label  = model.names[cls_id]

                # Detect buses (class 5) AND cars (class 2) for testing
                if label not in ("bus", "car", "truck"):
                    continue
                    
                found_vehicle = True

                x1,y1,x2,y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                # Try to read plate from this detection
                plate = process_bus(frame, (x1,y1,x2,y2), frame.shape[0])

                # Draw bounding box
                state = bus_state.get(plate, "outside") if plate else "outside"
                color = (0, 255, 0) if state == "inside" else (0, 165, 255)
                cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                label_text = f"{label} {conf:.0%}"
                if plate:
                    label_text += f" | {plate}"
                if SHOW_CAMERA_TEXT_OVERLAY:
                    cv2.putText(frame, label_text, (x1, y1-8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Fallback for Notepad testing: if no vehicle is found, check whole frame every 15 frames
            if not found_vehicle and frame_count % 15 == 0:
                h, w = frame.shape[:2]
                # Simulate bounding box across whole frame so center triggers the lines
                plate = process_bus(frame, (0, 0, w, h), h)
                if plate:
                    # Draw a rectangle around the whole frame to indicate we found text
                    cv2.rectangle(frame, (10, 10), (w-10, h-10), (255, 0, 255), 2)
                    if SHOW_CAMERA_TEXT_OVERLAY:
                        cv2.putText(frame, f"TEXT FOUND | {plate}", (20, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

        # Draw UI elements
        if SHOW_CAMERA_TEXT_OVERLAY and ENTRY_LINE_Y:
            draw_ui(frame, [])

        cv2.imshow("Bus Tracker - Press Q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    print("Stopped.")

if __name__ == "__main__":
    main()
