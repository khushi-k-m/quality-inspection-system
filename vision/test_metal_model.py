from pathlib import Path
from ultralytics import YOLO

# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    ROOT_DIR
    / "trained_model"
    / "metal_surface_model"
    / "weights"
    / "best.pt"
)

TEST_IMAGES_DIR = ROOT_DIR / "vision" / "test_images"

# ============================================================
# CHECK PATHS
# ============================================================

print("=" * 70)
print("        METAL SURFACE DEFECT DETECTION")
print("=" * 70)

print(f"Model:       {MODEL_PATH}")
print(f"Test folder: {TEST_IMAGES_DIR}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found:\n{MODEL_PATH}"
    )

if not TEST_IMAGES_DIR.exists():
    raise FileNotFoundError(
        f"Test images folder not found:\n{TEST_IMAGES_DIR}"
    )

# ============================================================
# FIND ALL IMAGES
# ============================================================

image_extensions = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}

test_images = [
    image
    for image in TEST_IMAGES_DIR.iterdir()
    if image.is_file()
    and image.suffix.lower() in image_extensions
]

if not test_images:
    raise FileNotFoundError(
        f"No test images found in:\n{TEST_IMAGES_DIR}"
    )

test_images.sort()

print(f"\nFound {len(test_images)} test images.")

# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading Metal Surface YOLO model...")

model = YOLO(str(MODEL_PATH))

print("Model loaded successfully.")

# ============================================================
# RUN DETECTION ON ALL IMAGES
# ============================================================

print("\n" + "=" * 70)
print("STARTING DETECTION")
print("=" * 70)

total_detections = 0

for index, image_path in enumerate(test_images, start=1):

    print("\n" + "-" * 70)
    print(f"IMAGE {index}/{len(test_images)}")
    print(f"File: {image_path.name}")
    print("-" * 70)

    results = model.predict(
        source=str(image_path),
        conf=0.25,
        save=True
    )

    image_has_detection = False

    for result in results:

        if result.boxes is None or len(result.boxes) == 0:
            print("No defects detected.")
            continue

        image_has_detection = True

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = model.names[class_id]

            total_detections += 1

            print(
                f"Detected: {class_name} | "
                f"Confidence: {confidence:.2f}"
            )

    if image_has_detection:
        print("Status: DEFECT DETECTED")
    else:
        print("Status: NO DEFECT DETECTED")

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("              TESTING COMPLETED")
print("=" * 70)

print(f"Images tested:      {len(test_images)}")
print(f"Total detections:   {total_detections}")

print("\nPrediction images have been saved automatically.")
print("Check the 'runs/detect/predict' folder.")

print("=" * 70)