import sys
import cv2
from ultralytics import YOLO
from pathlib import Path
from datetime import datetime
import time

# ======================================================
# PROJECT PATH
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

# Allow importing from project root
sys.path.insert(0, str(ROOT_DIR))

from quality.inspector import save_inspection
from reports.generate_report import generate_report


# ======================================================
# PATHS
# ======================================================

MODEL_PATH = (
    ROOT_DIR
    / "trained_model"
    / "steel_defect_model"
    / "weights"
    / "best.pt"
)

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
    sys.exit()


print(f"✅ Camera Connected (Index {camera_index})")

print("\nPress S -> Save Inspection")
print("Press Q -> Quit\n")


# ======================================================
# FULL SCREEN WINDOW
# ======================================================

WINDOW_NAME = "Steel Quality Inspection System"

cv2.namedWindow(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN
)

cv2.setWindowProperty(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)


# ======================================================
# LIVE DETECTION
# ======================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print("❌ Failed to read frame.")
        break


    start_time = time.time()


    # ==================================================
    # YOLO DETECTION
    # ==================================================

    results = model(
        frame,
        imgsz=320,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    result = results[0]

    annotated = result.plot()


    # ==================================================
    # FPS
    # ==================================================

    elapsed = time.time() - start_time

    fps = (
        1 / elapsed
        if elapsed > 0
        else 0
    )


    # ==================================================
    # DEFECT COUNT
    # ==================================================

    boxes = result.boxes

    total_defects = len(boxes)


    # ==================================================
    # DEFECT TYPES
    # ==================================================

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


    # ==================================================
    # QUALITY DECISION
    # ==================================================

    if total_defects == 0:

        status = "PASS"
        status_color = (0, 255, 0)

    elif (
        defect_count["Rust"] > 0
        or total_defects > 2
    ):

        status = "FAIL"
        status_color = (0, 0, 255)

    else:

        status = "REWORK"
        status_color = (0, 165, 255)


    # ==================================================
    # INSPECTION INFORMATION
    # ==================================================

    now = datetime.now()

    timestamp = now.strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    inspection_id = now.strftime(
        "INSP%Y%m%d%H%M%S%f"
    )[:-3]


    # ==================================================
    # INFORMATION PANEL
    # ==================================================

    cv2.rectangle(
        annotated,
        (15, 15),
        (390, 330),
        (30, 30, 30),
        -1
    )


    cv2.putText(
        annotated,
        "AI STEEL QUALITY INSPECTION",
        (25, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        annotated,
        f"ID: {inspection_id}",
        (25, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1
    )


    cv2.putText(
        annotated,
        f"FPS: {fps:.2f}",
        (25, 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2
    )


    cv2.putText(
        annotated,
        f"STATUS: {status}",
        (25, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.70,
        status_color,
        2
    )


    cv2.putText(
        annotated,
        f"Total Defects: {total_defects}",
        (25, 175),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


    cv2.putText(
        annotated,
        f"Scratches: {defect_count['Scratches']}",
        (25, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        1
    )


    cv2.putText(
        annotated,
        f"Dents: {defect_count['Dents']}",
        (25, 235),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        1
    )


    cv2.putText(
        annotated,
        f"Rust: {defect_count['Rust']}",
        (25, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        1
    )


    cv2.putText(
        annotated,
        f"Other: {defect_count['Other']}",
        (25, 285),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        1
    )


    cv2.putText(
        annotated,
        timestamp,
        (25, 315),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (180, 180, 180),
        1
    )


    # ==================================================
    # DISPLAY
    # ==================================================

    cv2.imshow(
        WINDOW_NAME,
        annotated
    )


    # ==================================================
    # KEYBOARD
    # ==================================================

    key = cv2.waitKey(1) & 0xFF


    # ==================================================
    # SAVE INSPECTION
    # ==================================================

    if key == ord("s"):

        filename = (
            OUTPUT_DIR
            / f"{inspection_id}_{status}.jpg"
        )


        # ----------------------------------------------
        # Save image
        # ----------------------------------------------

        success = cv2.imwrite(
            str(filename),
            annotated
        )


        if success:

            print("\n======================================")
            print("INSPECTION SAVED")
            print("======================================")

            print(
                f"Inspection ID : {inspection_id}"
            )

            print(
                f"Status        : {status}"
            )

            print(
                f"Scratches     : "
                f"{defect_count['Scratches']}"
            )

            print(
                f"Dents         : "
                f"{defect_count['Dents']}"
            )

            print(
                f"Rust          : "
                f"{defect_count['Rust']}"
            )

            print(
                f"Other         : "
                f"{defect_count['Other']}"
            )

            print(
                f"Total Defects : {total_defects}"
            )

            print(
                f"Image         : {filename}"
            )


            # ------------------------------------------
            # Save database record
            # ------------------------------------------

            try:

                save_inspection(

                    inspection_id=inspection_id,

                    timestamp=timestamp,

                    image_path=str(filename),

                    scratches=defect_count["Scratches"],

                    dents=defect_count["Dents"],

                    rust=defect_count["Rust"],

                    other=defect_count["Other"],

                    total_defects=total_defects,

                    status=status,

                    inspector="Operator-1"
                )

                # ------------------------------------------
                # GENERATE AUTOMATIC PDF REPORT
                # ------------------------------------------

                try:

                    generate_report()

                    print("✅ PDF inspection report generated automatically.")

                except Exception as error:

                    print("❌ PDF report generation failed:")
                    print(error)

                print("✅ Database record saved.")

            except Exception as error:

                print("❌ Database error:")
                print(error)


            print(
                "======================================\n"
            )


        else:

            print(
                "❌ Failed to save image."
            )


    # ==================================================
    # QUIT
    # ==================================================

    elif key == ord("q"):

        print("\nClosing Camera...")
        break


# ======================================================
# CLEANUP
# ======================================================

cap.release()

cv2.destroyAllWindows()

print("✅ Camera Closed Successfully.")