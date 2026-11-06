from __future__ import annotations

import argparse
import csv
import hashlib
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REVIEW_ROOT = Path(__file__).resolve().parent
BATCH_PATH = REVIEW_ROOT / "review_batch.csv"
MANIFEST_PATH = REVIEW_ROOT / "review_manifest.csv"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
BATCH_SIZE_PER_SOURCE = 12
SEED = 20261001
SOURCES = (
    "dataset",
    "dataset_metal",
    "dataset_fabric",
    "dataset_pcb_boards",
    "dataset_welding",
    "dataset_wood_surface",
)
FIELDS = ("image_path", "material_class", "source_dataset", "review_status", "review_reason")


def image_family(path: Path) -> str:
    name = path.name.lower()
    for marker in ("_jpg.rf.", "_jpeg.rf.", "_png.rf.", ".rf."):
        if marker in name:
            return name.split(marker, 1)[0]
    return path.stem.lower()


def read_hash(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


def source_images(source: str) -> list[Path]:
    root = PROJECT_ROOT / source
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and "images" in path.parts
    )


def prepare(force: bool) -> None:
    if BATCH_PATH.exists() and not force:
        raise SystemExit(f"{BATCH_PATH.name} already exists; keep it or rerun with --force before any reviews.")

    rng = random.Random(SEED)
    globally_seen_hashes: set[str] = set()
    rows: list[dict[str, str]] = []
    invalid_count = 0
    duplicate_count = 0

    for source in SOURCES:
        families: dict[str, list[Path]] = defaultdict(list)
        for path in source_images(source):
            families[image_family(path)].append(path)

        family_keys = list(families)
        rng.shuffle(family_keys)
        selected = 0
        for family_key in family_keys:
            variants = families[family_key]
            rng.shuffle(variants)
            for path in variants:
                digest = read_hash(path)
                if digest is None:
                    invalid_count += 1
                    continue
                if digest in globally_seen_hashes:
                    duplicate_count += 1
                    continue
                globally_seen_hashes.add(digest)
                rows.append(
                    {
                        "image_path": path.relative_to(PROJECT_ROOT).as_posix(),
                        "material_class": "",
                        "source_dataset": source,
                        "review_status": "pending",
                        "review_reason": "",
                    }
                )
                selected += 1
                break
            if selected >= BATCH_SIZE_PER_SOURCE:
                break
        print(f"{source}: {selected} pending candidates")

    with BATCH_PATH.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    if not MANIFEST_PATH.exists():
        with MANIFEST_PATH.open("w", newline="", encoding="utf-8-sig") as output:
            csv.DictWriter(output, fieldnames=FIELDS).writeheader()

    print(f"Prepared {len(rows)} pending candidates in {BATCH_PATH}")
    print(f"Skipped unreadable files: {invalid_count}; exact duplicates skipped: {duplicate_count}")
    print("No labels were assigned and no source images were copied.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a small, unlabeled manual review batch.")
    parser.add_argument("--force", action="store_true", help="Replace the pending batch CSV; does not clear the review manifest.")
    args = parser.parse_args()
    prepare(force=args.force)


if __name__ == "__main__":
    main()
