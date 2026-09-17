from pathlib import Path
from ultralytics import YOLO
import cv2
import shutil


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    ROOT_DIR
    / "trained_model"
    / "pcb_boards_model"
    / "weights"
    / "best.pt"
)

TEST_DIR = (
    ROOT_DIR
    / "vision"
    / "test_images"
    / "pcb_test"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "output"
    / "pcb_test"
)


# ============================================================
# SETTINGS
# ============================================================

CONFIDENCE = 0.25
IMAGE_SIZE = 640

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# HEADER
# ============================================================

print("=" * 65)
print("PCB BOARD DEFECT DETECTION")
print("=" * 65)

print(f"Model : {MODEL_PATH}")
print(f"Images: {TEST_DIR}")
print(f"Output: {OUTPUT_DIR}")
print()


# ============================================================
# CHECK MODEL
# ============================================================

if not MODEL_PATH.exists():
    print("ERROR: Model not found!")
    print()
    print("Expected model:")
    print(MODEL_PATH)
    print()
    print("Please check the location of best.pt.")
    raise SystemExit(1)


# ============================================================
# CHECK TEST FOLDER
# ============================================================

if not TEST_DIR.exists():
    print("ERROR: Test image folder not found!")
    print()
    print("Create this folder:")
    print(TEST_DIR)
    raise SystemExit(1)


# ============================================================
# FIND ALL IMAGES
# ============================================================

image_files = sorted(
    [
        file
        for file in TEST_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
)


print(f"Test images found: {len(image_files)}")
print()


if len(image_files) == 0:
    print("ERROR: No test images found.")
    print()
    print("Put your PCB test images inside:")
    print(TEST_DIR)
    raise SystemExit(1)


# ============================================================
# PREPARE OUTPUT
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Remove previous prediction images
for old_file in OUTPUT_DIR.iterdir():
    if old_file.is_file():
        old_file.unlink()


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading trained PCB YOLO model...")

model = YOLO(str(MODEL_PATH))

print("Model loaded successfully.")
print()

print("Classes in trained model:")

for class_id, class_name in model.names.items():
    print(f"  {class_id}: {class_name}")

print()


# ============================================================
# DETECTION
# ============================================================

print("=" * 65)
print("STARTING PCB DETECTION")
print("=" * 65)
print()


total_images = 0
total_detections = 0


for index, image_path in enumerate(image_files, start=1):

    print(
        f"[{index}/{len(image_files)}] "
        f"{image_path.name}"
    )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image = cv2.imread(str(image_path))

    if image is None:
        print("  ERROR: Could not read image.")
        print()
        continue

    total_images += 1

    # --------------------------------------------------------
    # Run YOLO
    # --------------------------------------------------------

    results = model.predict(
        source=str(image_path),
        conf=CONFIDENCE,
        imgsz=IMAGE_SIZE,
        device="cpu",
        verbose=False
    )

    result = results[0]

    # --------------------------------------------------------
    # Get annotated image
    # --------------------------------------------------------

    annotated_image = result.plot()

    # --------------------------------------------------------
    # Save prediction
    # --------------------------------------------------------

    output_path = OUTPUT_DIR / image_path.name

    cv2.imwrite(
        str(output_path),
        annotated_image
    )

    # --------------------------------------------------------
    # Detection information
    # --------------------------------------------------------

    if result.boxes is None or len(result.boxes) == 0:

        print("  No defects detected.")

    else:

        detections_in_image = len(result.boxes)

        total_detections += detections_in_image

        print(
            f"  Defects detected: "
            f"{detections_in_image}"
        )

        for box in result.boxes:

            class_id = int(box.cls[0])

            confidence = float(box.conf[0])

            class_name = model.names[class_id]

            print(
                f"    - {class_name}"
                f" | Confidence: "
                f"{confidence:.2f}"
            )

    print(
        f"  Saved: {output_path}"
    )

    print()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("=" * 65)
print("PCB DETECTION COMPLETED")
print("=" * 65)

print()
print(f"Images processed : {total_images}")
print(f"Total detections : {total_detections}")
print()
print(f"Prediction images:")
print(OUTPUT_DIR)

print()
print("=" * 65)