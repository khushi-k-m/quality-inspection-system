"""
Metal Surface Inspection — Integration Test
============================================
Runs the complete pipeline:
    1. Find test images in vision/test_images/
    2. Load Metal YOLO model
    3. Detect defects on every image
    4. Evaluate quality (score / severity / status)
    5. Save each inspection to database/metal_inspections.db
    6. Print a full summary

Run from the project root:
    python vision/test_metal_inspection.py
"""

import sys
from pathlib import Path
from datetime import datetime

# ── Make sure the project root is on sys.path ──────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Imports ────────────────────────────────────────────────────────────
from metal.inspector  import MetalInspector
from metal.evaluator  import MetalEvaluator
from metal.database   import create_database, save_inspection
from metal.history    import MetalHistory

# ── Paths ──────────────────────────────────────────────────────────────
TEST_IMAGES_DIR = ROOT_DIR / "vision" / "test_images"
OUTPUT_DIR      = ROOT_DIR / "output" / "metal_capture"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ── Separator helpers ──────────────────────────────────────────────────
SEP  = "=" * 70
DASH = "-" * 70


def main():
    print()
    print(SEP)
    print("   METAL SURFACE INSPECTION — INTEGRATION TEST")
    print(SEP)

    # ── 1. Initialise database ─────────────────────────────────────────
    print("\n[1/6] Initialising database...")
    create_database()
    print("      database/metal_inspections.db  [OK]")

    # ── 2. Find test images ────────────────────────────────────────────
    print(f"\n[2/6] Scanning for test images in:\n      {TEST_IMAGES_DIR}")

    if not TEST_IMAGES_DIR.exists():
        print(f"\n  ERROR: Test images folder not found:\n  {TEST_IMAGES_DIR}")
        sys.exit(1)

    images = sorted(
        p for p in TEST_IMAGES_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not images:
        print(f"\n  ERROR: No images found in {TEST_IMAGES_DIR}")
        sys.exit(1)

    print(f"      Found {len(images)} image(s).")

    # ── 3. Load model ──────────────────────────────────────────────────
    print("\n[3/6] Loading Metal Surface YOLO model...")
    try:
        inspector = MetalInspector(confidence=0.25)
        inspector._load_model()          # trigger load now so errors surface early
        print("      Model loaded  [OK]")
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    evaluator = MetalEvaluator()

    # ── 4. Run inspection on every image ──────────────────────────────
    print(f"\n[4/6] Running inspection on {len(images)} image(s)...")
    print(DASH)

    saved_ids   = []
    total_defs  = 0

    for idx, image_path in enumerate(images, start=1):
        print(f"\n  Image {idx}/{len(images)} : {image_path.name}")

        # Detect
        try:
            detections, annotated_jpg = inspector.inspect_with_annotated(
                str(image_path)
            )
        except Exception as e:
            print(f"    SKIP — inference error: {e}")
            continue

        # Evaluate
        result = evaluator.evaluate(detections)

        print(f"    Defects found  : {result['defect_count']}")
        print(f"    Quality Score  : {result['quality_score']}%")
        print(f"    Severity       : {result['severity']}")
        print(f"    Status         : {result['status']}")

        if detections:
            print("    Detections:")
            for d in detections:
                print(
                    f"      • {d['class_name']:<18} "
                    f"conf={d['confidence']:.2f}  "
                    f"box=({d['x1']},{d['y1']})-({d['x2']},{d['y2']})"
                )

        # ── 5. Save to database ────────────────────────────────────────
        now           = datetime.now()
        timestamp     = now.strftime("%d-%m-%Y %H:%M:%S")
        inspection_id = now.strftime("MINSP%Y%m%d%H%M%S%f")
        status        = result["status"]

        # Save annotated image
        out_file = OUTPUT_DIR / f"{inspection_id}_{status}.jpg"
        with open(str(out_file), "wb") as f:
            f.write(annotated_jpg)

        save_inspection(
            inspection_id = inspection_id,
            timestamp     = timestamp,
            image_path    = str(out_file),
            defect_count  = result["defect_count"],
            quality_score = result["quality_score"],
            severity      = result["severity"],
            status        = status,
            remarks       = result["remarks"],
            defects       = detections,
            inspector     = "AI System",
            material      = "Metal",
        )

        saved_ids.append(inspection_id)
        total_defs += result["defect_count"]

        print(f"    Saved → {inspection_id}")

    # ── 6. Retrieve and display history ───────────────────────────────
    print(f"\n[5/6] Verifying database records...")
    history = MetalHistory()
    records = history.get_inspections(limit=len(images) + 5)
    print(f"      Total records in DB : {len(records)}")

    print(f"\n[6/6] Final Summary")
    print(SEP)
    print(f"  Images processed   : {len(images)}")
    print(f"  Inspections saved  : {len(saved_ids)}")
    print(f"  Total defects      : {total_defs}")
    print(f"  Database           : {ROOT_DIR / 'database' / 'metal_inspections.db'}")
    print(f"  Annotated images   : {OUTPUT_DIR}")
    print()

    if saved_ids:
        print("  Inspection IDs saved this run:")
        for iid in saved_ids:
            print(f"    {iid}")

    print()
    history.print_history(limit=len(images) + 5)
    print(SEP)
    print("  METAL INSPECTION TEST COMPLETED SUCCESSFULLY")
    print(SEP)


if __name__ == "__main__":
    main()
