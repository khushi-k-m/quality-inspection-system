import cv2

cap = cv2.VideoCapture(0)

print("Opened:", cap.isOpened())

while True:
    ret, frame = cap.read()

    print("ret =", ret)

    if not ret:
        print("Failed to read frame")
        continue

    cv2.imshow("Camera Test", frame)

    key = cv2.waitKey(1)

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()