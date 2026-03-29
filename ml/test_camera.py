import cv2

print("Testing camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow to bypass MSMF grab errors

if not cap.isOpened():
    print("ERROR: Camera not found!")
    print("Try changing 0 to 1 or 2 in VideoCapture(0)")
else:
    print("Camera opened successfully!")
    print("Press Q to quit")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Cannot read frame")
        break

    cv2.putText(frame, "Camera Working! Press Q to quit",
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2)
    cv2.imshow("Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Done.")
