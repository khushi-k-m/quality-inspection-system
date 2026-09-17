from pathlib import Path
from ultralytics import YOLO
import cv2


# ============================================================
# FABRIC SURFACE DEFECT DETECTION - TEST SCRIPT
# ============================================================

print("=" * 60)
print("FABRIC SURFACE DEFECT DETECTION")
print("=" * 60)


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    ROOT_DIR
    / "trained_model"
    / "fabrics_defect_model"
    / "weights"
    / "best.pt"
)

TEST_IMAGE_DIR = (
    ROOT_DIR
    / "vision"
    / "test_images"
    / "fabrics_test"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "output"
    / "fabrics_test"
)


print(f"Model : {MODEL_PATH}")
print(f"Images: {TEST_IMAGE_DIR}")
print(f"Output: {OUTPUT_DIR}")
print()


# ============================================================
# CHECK MODEL
# ============================================================

if not MODEL_PATH.exists():
    print("[ERROR] Trained model not found!")
    print(MODEL_PATH)
    raise SystemExit(1)


# ============================================================
# CHECK TEST IMAGE FOLDER
# ============================================================

if not TEST_IMAGE_DIR.exists():
    print("[ERROR] Test image folder not found!")
    print(TEST_IMAGE_DIR)
    raise SystemExit(1)


# ============================================================
# FIND ALL IMAGES
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}

image_paths = sorted(
    [
        path
        for path in TEST_IMAGE_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
)


if len(image_paths) == 0:
    print("[ERROR] No test images found!")
    print(TEST_IMAGE_DIR)
    raise SystemExit(1)


print(f"Test images found: {len(image_paths)}")
print()


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading trained Fabric YOLO model...")

model = YOLO(str(MODEL_PATH))

print("Model loaded successfully.")
print()

# Display classes from trained model
print("MODEL CLASSES:")
for class_id, class_name in model.names.items():
    print(f"  {class_id}: {class_name}")

print()


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DETECTION SETTINGS
# ============================================================

CONFIDENCE_THRESHOLD = 0.25
IMAGE_SIZE = 640

# Current VS Code environment has CPU-only PyTorch
DEVICE = "cpu"


# ============================================================
# STATISTICS
# ============================================================

total_images = len(image_paths)
images_with_defects = 0
images_without_defects = 0
total_defects = 0

class_counts = {}


# ============================================================
# START DETECTION
# ============================================================

print("=" * 60)
print("STARTING FABRIC DETECTION")
print("=" * 60)
print()


for index, image_path in enumerate(image_paths, start=1):

    print(
        f"[{index}/{total_images}] {image_path.name}"
    )

    try:

        # ----------------------------------------------------
        # RUN YOLO
        # ----------------------------------------------------

        results = model.predict(
            source=str(image_path),
            imgsz=IMAGE_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            device=DEVICE,
            verbose=False
        )

        result = results[0]

        # ----------------------------------------------------
        # NO DETECTIONS
        # ----------------------------------------------------

        if result.boxes is None or len(result.boxes) == 0:

            print("    No defects detected.")

            images_without_defects += 1

        # ----------------------------------------------------
        # DETECTIONS FOUND
        # ----------------------------------------------------

        else:

            defect_count = len(result.boxes)

            images_with_defects += 1
            total_defects += defect_count

            print(
                f"    Defects detected: {defect_count}"
            )

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                class_name = model.names[class_id]

                # Count class
                if class_name not in class_counts:
                    class_counts[class_name] = 0

                class_counts[class_name] += 1

                print(
                    f"       - {class_name}"
                    f" | Confidence: {confidence:.2f}"
                )

        # ----------------------------------------------------
        # SAVE ANNOTATED IMAGE
        # ----------------------------------------------------

        annotated_image = result.plot()

        output_path = OUTPUT_DIR / image_path.name

        cv2.imwrite(
            str(output_path),
            annotated_image
        )

        print(
            f"    Saved: {output_path.name}"
        )

    except Exception as error:

        print(
            f"    [ERROR] Failed to process image: "
            f"{error}"
        )

    print()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("=" * 60)
print("FABRIC DETECTION COMPLETED")
print("=" * 60)

print()

print(f"Total images tested       : {total_images}")
print(f"Images with defects      : {images_with_defects}")
print(f"Images without defects   : {images_without_defects}")
print(f"Total defects detected   : {total_defects}")

print()


# ============================================================
# CLASS SUMMARY
# ============================================================

print("=" * 60)
print("DEFECT CLASS SUMMARY")
print("=" * 60)

if class_counts:

    for class_name, count in sorted(
        class_counts.items()
    ):
        print(
            f"{class_name:<25} : {count}"
        )

else:

    print("No defects detected.")


# ============================================================
# OUTPUT LOCATION
# ============================================================

print()

print("=" * 60)
print("OUTPUT")
print("=" * 60)

print(
    f"Annotated images saved to:"
)

print(OUTPUT_DIR)

print()

print("=" * 60)
print("TEST FINISHED")
print("=" * 60)