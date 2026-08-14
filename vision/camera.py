import sys
import time
import cv2

from pathlib import Path
from datetime import datetime

from ultralytics import YOLO


# ======================================================
# PROJECT ROOT
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ======================================================
# PROJECT IMPORTS
# ======================================================

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

OUTPUT_DIR = (
    ROOT_DIR
    / "output"
    / "camera_capture"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ======================================================
# SETTINGS
# ======================================================

CONFIDENCE_THRESHOLD = 0.40
IMAGE_SIZE = 320

WINDOW_NAME = "Steel Quality Inspection System"


# ======================================================
# LOAD MODEL
# ======================================================

print("=" * 50)
print("Loading Steel Defect Detection Model...")
print("=" * 50)

if not MODEL_PATH.exists():

    print("❌ Model not found:")
    print(MODEL_PATH)

    sys.exit(1)


try:

    model = YOLO(str(MODEL_PATH))

    print("✅ YOLO Model Loaded")

except Exception as e:

    print("❌ Model loading failed:")
    print(e)

    sys.exit(1)


# ======================================================
# OPEN CAMERA
# ======================================================

cap = None
camera_index = -1

for i in range(5):

    print(f"Trying Camera {i}...")

    test = cv2.VideoCapture(
        i,
        cv2.CAP_DSHOW
    )

    if not test.isOpened():

        test.release()
        continue

    time.sleep(1)

    test.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280
    )

    test.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720
    )

    working = False

    for _ in range(10):

        ret, frame = test.read()

        if ret and frame is not None:

            working = True
            break

        time.sleep(0.1)

    if working:

        cap = test
        camera_index = i
        break

    test.release()


if cap is None:

    print()
    print("❌ Camera could not be opened.")
    print("Close other applications using the webcam.")
    sys.exit(1)


print()
print(f"✅ Camera Connected (Index {camera_index})")

print()
print("==============================================")
print("CAMERA CONTROLS")
print("==============================================")
print("S  -> Save Inspection")
print("Q  -> Quit")
print("ESC -> Quit")
print("==============================================")
print()


# ======================================================
# CREATE WINDOW
# ======================================================

cv2.namedWindow(
    WINDOW_NAME,
    cv2.WINDOW_NORMAL
)

# Maximize instead of using OpenCV fullscreen.
# This keeps keyboard input more reliable on Windows.

try:

    cv2.setWindowProperty(
        WINDOW_NAME,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_NORMAL
    )

except Exception:
    pass


# ======================================================
# MAIN LOOP
# ======================================================

try:

    while True:

        # ----------------------------------------------
        # READ CAMERA
        # ----------------------------------------------

        ret, frame = cap.read()

        if not ret or frame is None:

            print("⚠️ Camera frame unavailable.")

            # Still process keyboard events
            key = cv2.waitKey(100)

            if key != -1:

                key = key & 0xFF

                if key in (
                    ord("q"),
                    ord("Q"),
                    27
                ):

                    print("Closing Camera...")
                    break

            continue


        # ----------------------------------------------
        # YOLO
        # ----------------------------------------------

        start_time = time.time()

        results = model(
            frame,
            imgsz=IMAGE_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False
        )

        result = results[0]

        annotated = result.plot()


        # ----------------------------------------------
        # FPS
        # ----------------------------------------------

        elapsed = time.time() - start_time

        fps = (
            1 / elapsed
            if elapsed > 0
            else 0
        )


        # ----------------------------------------------
        # DEFECT COUNT
        # ----------------------------------------------

        boxes = result.boxes

        total_defects = len(boxes)

        defect_count = {
            "Scratches": 0,
            "Dents": 0,
            "Rust": 0,
            "Other": 0
        }


        for box in boxes:

            cls = int(box.cls[0])

            if cls == 0:

                defect_count["Scratches"] += 1

            elif cls == 1:

                defect_count["Dents"] += 1

            elif cls == 2:

                defect_count["Rust"] += 1

            elif cls == 3:

                defect_count["Other"] += 1


        # ----------------------------------------------
        # QUALITY EVALUATION
        # ----------------------------------------------

        if total_defects == 0:

            quality_score = 100
            status = "PASS"
            severity = "NONE"

            remarks = (
                "No visible defects detected. "
                "Product meets quality requirements."
            )

            status_color = (0, 255, 0)


        elif defect_count["Rust"] > 0:

            quality_score = 75
            status = "FAIL"
            severity = "HIGH"

            remarks = (
                "Rust detected. Product requires "
                "immediate quality review."
            )

            status_color = (0, 0, 255)


        elif total_defects > 2:

            quality_score = 65
            status = "FAIL"
            severity = "HIGH"

            remarks = (
                "Multiple defects detected. "
                "Product does not meet quality requirements."
            )

            status_color = (0, 0, 255)


        else:

            quality_score = 85
            status = "REWORK"
            severity = "MEDIUM"

            remarks = (
                "Minor defects detected. "
                "Product requires rework."
            )

            status_color = (0, 165, 255)


        # ----------------------------------------------
        # DISPLAY INFORMATION
        # ----------------------------------------------

        cv2.rectangle(
            annotated,
            (20, 20),
            (400, 315),
            (30, 30, 30),
            -1
        )


        cv2.putText(
            annotated,
            "AI STEEL QUALITY INSPECTION",
            (35, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            (255, 255, 255),
            2
        )


        cv2.putText(
            annotated,
            f"FPS: {fps:.1f}",
            (35, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2
        )


        cv2.putText(
            annotated,
            f"STATUS: {status}",
            (35, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            status_color,
            2
        )


        cv2.putText(
            annotated,
            f"QUALITY: {quality_score}%",
            (35, 153),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2
        )


        cv2.putText(
            annotated,
            f"DEFECTS: {total_defects}",
            (35, 186),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2
        )


        cv2.putText(
            annotated,
            f"Scratches: {defect_count['Scratches']}",
            (35, 218),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (220, 220, 220),
            1
        )


        cv2.putText(
            annotated,
            f"Dents: {defect_count['Dents']}",
            (190, 218),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (220, 220, 220),
            1
        )


        cv2.putText(
            annotated,
            f"Rust: {defect_count['Rust']}",
            (35, 248),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (220, 220, 220),
            1
        )


        cv2.putText(
            annotated,
            f"Other: {defect_count['Other']}",
            (190, 248),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (220, 220, 220),
            1
        )


        cv2.putText(
            annotated,
            f"SEVERITY: {severity}",
            (35, 282),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            status_color,
            2
        )


        # ----------------------------------------------
        # CONTROL MESSAGE
        # ----------------------------------------------

        cv2.putText(
            annotated,
            "S = SAVE INSPECTION     Q = QUIT",
            (35, 305),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (255, 255, 255),
            1
        )


        # ----------------------------------------------
        # SHOW
        # ----------------------------------------------

        cv2.imshow(
            WINDOW_NAME,
            annotated
        )


        # IMPORTANT:
        # waitKey must run AFTER imshow.
        # It is what allows OpenCV to receive keyboard events.

        key = cv2.waitKey(1) & 0xFF


        # ----------------------------------------------
        # DEBUG KEY
        # ----------------------------------------------

        if key != 255:

            print(
                f"Key detected: {key}"
            )


        # ----------------------------------------------
        # Q / ESC
        # ----------------------------------------------

        if key == ord("q"):

            print()
            print("Q pressed.")
            print("Closing Camera...")
            break


        if key == ord("Q"):

            print()
            print("Q pressed.")
            print("Closing Camera...")
            break


        if key == 27:

            print()
            print("ESC pressed.")
            print("Closing Camera...")
            break


        # ----------------------------------------------
        # S - SAVE
        # ----------------------------------------------

        if key == ord("s") or key == ord("S"):

            # Create ID ONLY when saving.
            # This keeps one inspection ID fixed.

            now = datetime.now()

            timestamp = now.strftime(
                "%d-%m-%Y %H:%M:%S"
            )

            inspection_id = now.strftime(
                "INSP%Y%m%d%H%M%S%f"
            )


            print()
            print("=" * 55)
            print("SAVING INSPECTION")
            print("=" * 55)


            # ==========================================
            # SAVE IMAGE
            # ==========================================

            filename = (
                OUTPUT_DIR
                / f"{inspection_id}_{status}.jpg"
            )


            if cv2.imwrite(
                str(filename),
                annotated
            ):

                print("✅ Image Saved")
                print(f"Image : {filename}")

            else:

                print("❌ Image could not be saved.")
                continue


            # ==========================================
            # DATABASE
            # ==========================================

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

                    quality_score=quality_score,

                    severity=severity,

                    remarks=remarks,

                    inspector="AI System"
                )


                print("✅ Database record saved")


            except Exception as e:

                print()
                print("❌ Database Error:")
                print(e)

                continue


            # ==========================================
            # AUTOMATIC PDF
            # ==========================================

            try:

                report_path = generate_report(
                    inspection_id
                )


                if report_path:

                    print("✅ PDF Report Generated")
                    print(
                        f"Report : {report_path}"
                    )


            except Exception as e:

                print()
                print("❌ PDF Report Error:")
                print(e)


            # ==========================================
            # FINAL
            # ==========================================

            print()
            print("=" * 55)
            print("✅ COMPLETE INSPECTION SAVED")
            print("=" * 55)

            print(
                f"Inspection ID : {inspection_id}"
            )

            print(
                f"Status        : {status}"
            )

            print(
                f"Quality Score : {quality_score}%"
            )

            print(
                f"Severity      : {severity}"
            )

            print(
                f"Defects       : {total_defects}"
            )

            print(
                f"Image         : {filename}"
            )

            print("=" * 55)
            print()


finally:

    # ==================================================
    # CLEANUP
    # ==================================================

    if cap is not None:

        cap.release()

    cv2.destroyAllWindows()

    print("✅ Camera Closed Successfully.")