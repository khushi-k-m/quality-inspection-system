import cv2
from ultralytics import YOLO
from pathlib import Path
from datetime import datetime
import time

# ======================================================
# PATHS
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = ROOT_DIR / "trained_model" / "steel_defect_model" / "weights" / "best.pt"

OUTPUT_DIR = ROOT_DIR / "output" / "camera_capture"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIDENCE_THRESHOLD = 0.40

# ======================================================
# LOAD MODEL
# ======================================================

print("=" * 50)
print("Loading Steel Defect Detection Model...")
print("=" * 50)

model = YOLO(str(MODEL_PATH))

# ======================================================
# FIND CAMERA
# ======================================================

cap = None
camera_index = -1

for i in range(5):
    test = cv2.VideoCapture(i, cv2.CAP_DSHOW)

    if test.isOpened():
        ret, frame = test.read()

        if ret:
            cap = test
            camera_index = i
            break

    test.release()

if cap is None:
    print("❌ No camera found.")
    exit()

print(f"✅ Camera Connected (Index {camera_index})")
print("\nPress S -> Save Image")
print("Press Q -> Quit\n")

# ======================================================
# LIVE DETECTION
# ======================================================
cv2.namedWindow("Steel Quality Inspection System", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(
    "Steel Quality Inspection System",
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to read frame.")
        break

    start = time.time()

    # -------------------------------
    # YOLO Prediction
    # -------------------------------

    results = model(
        frame,
        imgsz=320,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    result = results[0]
    annotated = result.plot()

    elapsed = time.time() - start
    fps = 1 / elapsed if elapsed > 0 else 0

    boxes = result.boxes
    total_defects = len(boxes)

    # -------------------------------
    # Count defect types
    # -------------------------------

    defect_count = {
        "Scratches": 0,
        "Dents": 0,
        "Rust": 0,
        "Other": 0
    }

    for box in boxes:

        cls = int(box.cls)

        if cls == 0:
            defect_count["Scratches"] += 1

        elif cls == 1:
            defect_count["Dents"] += 1

        elif cls == 2:
            defect_count["Rust"] += 1

        elif cls == 3:
            defect_count["Other"] += 1

    # -------------------------------
    # Quality Decision
    # -------------------------------

    if total_defects == 0:

        status = "PASS"
        color = (0, 255, 0)

    elif defect_count["Rust"] > 0 or total_defects > 2:

        status = "FAIL"
        color = (0, 0, 255)

    else:

        status = "REWORK"
        color = (0, 165, 255)

    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    inspection_id = datetime.now().strftime("INSP%Y%m%d%H%M%S")

    # ======================================================
    # INFORMATION PANEL
    # ======================================================

    cv2.rectangle(
    annotated,
    (15, 15),
    (300, 215),
    (30, 30, 30),
    -1
)

    cv2.putText(
        annotated,
        "AI STEEL QUALITY INSPECTION SYSTEM",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        f"Inspection ID : {inspection_id}",
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1,
    )

    cv2.putText(
        annotated,
        f"FPS : {fps:.2f}",
        (20, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        f"Status : {status}",
        (20, 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
    )

    cv2.putText(
        annotated,
        f"Total Defects : {total_defects}",
        (20, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        f"Scratches : {defect_count['Scratches']}",
        (20, 185),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        f"Dents : {defect_count['Dents']}",
        (20, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        f"Rust : {defect_count['Rust']}",
        (20, 235),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        f"Other : {defect_count['Other']}",
        (20, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        annotated,
        timestamp,
        (20, 295),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (180, 180, 180),
        1,
    )

    # ======================================================
    # DISPLAY
    # ======================================================

    cv2.imshow("Steel Quality Inspection System", annotated)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):

        filename = OUTPUT_DIR / f"{inspection_id}_{status}.jpg"

        cv2.imwrite(str(filename), annotated)

        print(f"✅ Image Saved : {filename}")

    elif key == ord("q"):

        print("\nClosing Camera...")
        break

# ======================================================
# CLEANUP
# ======================================================

cap.release()
cv2.destroyAllWindows()

print("✅ Camera Closed Successfully.")