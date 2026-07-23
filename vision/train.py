from ultralytics import YOLO
from pathlib import Path

# ==================================================
# Configuration
# ==================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_NAME = "yolov8n.pt"
DATASET_PATH = ROOT_DIR / "dataset" / "data.yaml"

PROJECT_NAME = ROOT_DIR / "trained_model"
EXPERIMENT_NAME = "steel_defect_model"

EPOCHS = 30
IMAGE_SIZE = 640
BATCH_SIZE = 8
DEVICE = "cpu"

# Resume checkpoint
LAST_CHECKPOINT = (
    PROJECT_NAME /
    EXPERIMENT_NAME /
    "weights" /
    "last.pt"
)


def main():

    print("=" * 60)
    print("      AI STEEL DEFECT DETECTION TRAINING")
    print("=" * 60)

    # Check dataset
    if not DATASET_PATH.exists():
        print(f"\n❌ Dataset not found:\n{DATASET_PATH}")
        return

    # Create output directory if needed
    PROJECT_NAME.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------
    # Resume Training
    # ------------------------------------------------
    if LAST_CHECKPOINT.exists():

        print("\nPrevious training found.")
        print("Resuming from last checkpoint...\n")

        model = YOLO(str(LAST_CHECKPOINT))

        model.train(resume=True)

    # ------------------------------------------------
    # Fresh Training
    # ------------------------------------------------
    else:

        print("\nNo previous checkpoint found.")
        print("Starting a new training...\n")

        model = YOLO(MODEL_NAME)

        model.train(
            data=str(DATASET_PATH),
            epochs=EPOCHS,
            imgsz=IMAGE_SIZE,
            batch=BATCH_SIZE,
            device=DEVICE,
            project=str(PROJECT_NAME),
            name=EXPERIMENT_NAME,
            exist_ok=True,
            workers=2,
        )

    print("\n==========================================")
    print("Training Finished Successfully!")
    print("==========================================")


if __name__ == "__main__":
    main()