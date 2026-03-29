from ultralytics import YOLO
import cv2

print("Downloading/loading YOLO model...")
model = YOLO("yolo11n.pt")  # auto-downloads on first run (~6MB)
print("YOLO loaded!")

# Test on webcam
cap = cv2.VideoCapture(0)
print("Press Q to quit")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Run detection
    results = model(frame, conf=0.4, verbose=False)

    # Draw boxes on frame
    annotated = results[0].plot()

    # Show what was detected
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        label  = model.names[cls_id]
        conf   = float(box.conf[0])
        print(f"Detected: {label} ({conf:.0%})")

    cv2.imshow("YOLO Detection", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
