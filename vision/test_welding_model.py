import cv2
from ultralytics import YOLO
from pathlib import Path
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    ROOT_DIR
    / "trained_model"
    / "welding_defect_model"
    / "weights"
    / "best.pt"
)

TEST_IMAGES_DIR = (
    ROOT_DIR
    / "vision"
    / "test_images"
    / "welding_test"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "output"
    / "welding_test"
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

print("=" * 60)
print("WELDING DEFECT DETECTION")
print("=" * 60)

print(f"Model : {MODEL_PATH}")
print(f"Images: {TEST_IMAGES_DIR}")
print(f"Output: {OUTPUT_DIR}")
print()


# ============================================================
# CHECK MODEL
# ============================================================

if not MODEL_PATH.exists():
    print("[ERROR] Model not found!")
    print(f"Expected location:")
    print(MODEL_PATH)
    raise SystemExit(1)


# ============================================================
# CHECK TEST IMAGE FOLDER
# ============================================================

if not TEST_IMAGES_DIR.exists():
    print("[ERROR] Test image folder not found!")
    print(f"Create this folder:")
    print(TEST_IMAGES_DIR)
    raise SystemExit(1)


# ============================================================
# FIND ALL IMAGES
# ============================================================

image_paths = sorted(
    [
        path
        for path in TEST_IMAGES_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
)


print(f"Test images found: {len(image_paths)}")
print()


if len(image_paths) == 0:
    print("[ERROR] No test images found.")
    print("Put welding images inside:")
    print(TEST_IMAGES_DIR)
    raise SystemExit(1)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading trained Welding YOLO model...")

try:
    model = YOLO(str(MODEL_PATH))

except Exception as error:
    print("[ERROR] Failed to load model.")
    print(error)
    raise SystemExit(1)


print("Model loaded successfully.")
print()

print("=" * 60)
print("MODEL CLASSES")
print("=" * 60)

for class_id, class_name in model.names.items():
    print(f"{class_id} -> {class_name}")

print()


# ============================================================
# DETECTION
# ============================================================

print("=" * 60)
print("STARTING WELDING DETECTION")
print("=" * 60)
print()


total_images = 0
total_detections = 0

detection_summary = {}

start_time = datetime.now()


for index, image_path in enumerate(image_paths, start=1):

    print(
        f"[{index}/{len(image_paths)}] "
        f"{image_path.name}"
    )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image = cv2.imread(str(image_path))

    if image is None:
        print("   [WARNING] Could not read image.")
        print()
        continue

    # --------------------------------------------------------
    # Run YOLO
    # --------------------------------------------------------

    try:

        results = model.predict(
            source=image,
            conf=CONFIDENCE,
            imgsz=IMAGE_SIZE,
            device="cpu",
            verbose=False
        )

    except Exception as error:

        print("   [ERROR] Detection failed.")
        print(f"   {error}")
        print()

        continue

    result = results[0]

    # --------------------------------------------------------
    # Get annotated image
    # --------------------------------------------------------

    annotated_image = result.plot()

    # --------------------------------------------------------
    # Save output
    # --------------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / f"{image_path.stem}_detected{image_path.suffix}"
    )

    cv2.imwrite(
        str(output_path),
        annotated_image
    )

    # --------------------------------------------------------
    # Process detections
    # --------------------------------------------------------

    image_detection_count = 0

    if result.boxes is not None:

        for box in result.boxes:

            class_id = int(
                box.cls[0].item()
            )

            confidence = float(
                box.conf[0].item()
            )

            class_name = model.names[class_id]

            image_detection_count += 1
            total_detections += 1

            if class_name not in detection_summary:
                detection_summary[class_name] = 0

            detection_summary[class_name] += 1

            print(
                f"   Detected: {class_name} "
                f"| Confidence: {confidence:.2f}"
            )

    if image_detection_count == 0:

        print("   No welding defect detected.")

    else:

        print(
            f"   Total detections: "
            f"{image_detection_count}"
        )

    print(
        f"   Saved: {output_path.name}"
    )

    print()

    total_images += 1


# ============================================================
# FINAL SUMMARY
# ============================================================

end_time = datetime.now()

duration = (
    end_time - start_time
).total_seconds()


print("=" * 60)
print("WELDING DETECTION COMPLETED")
print("=" * 60)

print()

print(f"Images processed : {total_images}")
print(f"Total detections : {total_detections}")
print(f"Processing time  : {duration:.2f} seconds")

print()

print("=" * 60)
print("DETECTION SUMMARY")
print("=" * 60)

if detection_summary:

    for class_name, count in sorted(
        detection_summary.items()
    ):
        print(
            f"{class_name}: {count}"
        )

else:

    print("No defects detected.")


print()

print("=" * 60)
print("OUTPUT LOCATION")
print("=" * 60)

print(OUTPUT_DIR)

print()

print("Open the output folder to see")
print("the annotated welding images.")

print("=" * 60)