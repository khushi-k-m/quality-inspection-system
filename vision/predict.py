from ultralytics import YOLO
from pathlib import Path

# ==============================
# Paths
# ==============================

ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = ROOT / "trained_model" / "steel_defect_model" / "weights" / "best.pt"

INPUT_FOLDER = ROOT / "vision" / "test_images"

OUTPUT_FOLDER = ROOT / "output"

OUTPUT_FOLDER.mkdir(exist_ok=True)

# ==============================

print("=" * 50)
print("Steel Defect Detection")
print("=" * 50)

model = YOLO(str(MODEL_PATH))

images = (
    list(INPUT_FOLDER.glob("*.jpg")) +
    list(INPUT_FOLDER.glob("*.jpeg")) +
    list(INPUT_FOLDER.glob("*.png"))
)

print(f"\nFound {len(images)} images.\n")

for image in images:

    print(f"Processing: {image.name}")

    results = model.predict(
        source=str(image),
        save=True,
        project=str(OUTPUT_FOLDER),
        name="predictions",
        exist_ok=True,
        conf=0.25
    )

print("\nDone.")
print(f"Results saved in:\n{OUTPUT_FOLDER}")