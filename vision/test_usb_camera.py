import cv2

for index in range(3):
    print(f"\nTrying Camera {index}")

    cap = cv2.VideoCapture(index, cv2.CAP_ANY)

    if not cap.isOpened():
        print("Cannot open camera")
        continue

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Cannot read frame")
            break

        cv2.imshow(f"Camera {index}", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()