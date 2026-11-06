from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from human_review_data import (
    APPROVED_MATERIALS,
    DATASET_DIR,
    MATERIAL_DECISIONS,
    PREPARATION_PATH,
    PROJECT_ROOT,
    DecisionValidationError,
    load_decisions,
    read_csv,
    summarize_decisions,
)

DECISIONS_PATH = DATASET_DIR / "human_review_decisions.csv"
PROGRESS_PATH = DATASET_DIR / "HUMAN_REVIEW_PROGRESS.md"
DUPLICATE_REPORT_PATH = DATASET_DIR / "DUPLICATE_REVIEW_REPORT.md"
READINESS_PATH = DATASET_DIR / "TRAINING_READINESS.md"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

def count_preparation_paths(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["image_path"] for row in rows)


def write_progress() -> dict[str, object]:
    preparation = read_csv(PREPARATION_PATH)
    decisions = load_decisions(DECISIONS_PATH)
    summary = summarize_decisions(preparation, decisions)
    status_counts = summary["status_counts"]
    class_counts = summary["material_counts"]
    evidence_count = summary["evidence_reference_count"]
    no_evidence = summary["no_evidence_count"]
    additional = summary["additional_verification_count"]
    steel_metal = summary["steel_metal_unresolved_count"]

    lines = [
        "# Human review progress",
        "",
        "Generated from `human_review_decisions.csv`; this report does not change "
        "review decisions or source images.",
        "",
        f"- Total images: **{summary['total']:,}**",
        f"- Reviewed: **{summary['reviewed']:,}**",
        f"- Not reviewed: **{summary['not_reviewed']:,}**",
        f"- Approved: **{status_counts['approved']:,}**",
        f"- Needs review: **{status_counts['needs_review']:,}**",
        f"- Rejected: **{status_counts['rejected']:,}**",
        "",
        "## Approved material decisions",
        "",
        "| Material | Approved images |",
        "|---|---:|",
    ]
    for material in MATERIAL_DECISIONS:
        count = (
            class_counts[material]
            if material in APPROVED_MATERIALS
            else status_counts["rejected"]
            if material == "Unusable"
            else status_counts["needs_review"]
            if material == "Needs Review"
            else 0
        )
        lines.append(f"| {material} | {count:,} |")

    lines.extend(
        [
            "",
            "## Evidence and follow-up",
            "",
            f"- Approved decisions with a non-`none` evidence reference: "
            f"**{evidence_count:,}**",
            f"- Approved images explicitly recorded with no evidence reference: "
            f"**{no_evidence:,}**",
            f"- Images requiring additional verification (non-approved decisions, "
            f"missing rationale, or no evidence reference): **{additional:,}**",
            f"- Unresolved Steel/Metal cases marked Needs Review with a related "
            f"rationale: **{steel_metal:,}**",
            "",
            "A value of `none` is not independent evidence. Steel and Metal still "
            "require traceable material evidence distinguishing steel from "
            "non-steel. This summary does not decide whether the dataset is ready "
            "for training; use `audit_human_review.py readiness` for that check.",
            "",
        ]
    )
    PROGRESS_PATH.write_text("\n".join(lines), encoding="utf-8")
    return summary


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def roboflow_family(path: Path) -> str:
    stem = path.stem.casefold()
    for marker in ("_jpg.rf.", "_jpeg.rf.", "_png.rf.", ".rf."):
        if marker in stem:
            return stem.split(marker, 1)[0]
    return ""


def write_duplicate_report() -> None:
    preparation = read_csv(PREPARATION_PATH)
    path_counts = count_preparation_paths(preparation)
    duplicate_paths = {
        path: count for path, count in path_counts.items() if count > 1
    }
    by_hash: dict[str, list[str]] = defaultdict(list)
    by_basename: dict[str, list[str]] = defaultdict(list)
    by_family: dict[tuple[str, str], list[str]] = defaultdict(list)
    missing: list[str] = []
    unreadable: list[str] = []
    images = [
        row["image_path"]
        for row in preparation
        if Path(row["image_path"]).suffix.lower() in IMAGE_EXTENSIONS
    ]

    for index, relative in enumerate(images, 1):
        image_path = (PROJECT_ROOT / relative).resolve()
        if not image_path.is_relative_to(PROJECT_ROOT) or not image_path.is_file():
            missing.append(relative)
            continue
        try:
            digest = sha256_file(image_path)
        except OSError as error:
            unreadable.append(f"{relative}: {error}")
            continue
        by_hash[digest].append(relative)
        by_basename[image_path.name.casefold()].append(relative)
        family = roboflow_family(image_path)
        if family:
            by_family[(relative.split("/", 1)[0], family)].append(relative)
        if index % 5000 == 0:
            print(f"Hashed {index:,}/{len(images):,} images", flush=True)

    identical_groups = {
        digest: paths for digest, paths in by_hash.items() if len(paths) > 1
    }
    basename_groups = {
        name: paths for name, paths in by_basename.items() if len(paths) > 1
    }
    family_groups = {
        key: paths for key, paths in by_family.items() if len(paths) > 1
    }

    lines = [
        "# Duplicate review report",
        "",
        "Generated from the source preparation manifest. This audit does not "
        "remove, move, or alter files. SHA-256 detects byte-identical files; "
        "same-name and Roboflow-family groups are review leads, not proof of "
        "pixel-identical or same-physical-item images.",
        "",
        "**Handling status:** NOT REVIEWED. A human must inspect every reported "
        "group and document whether it represents the same physical item before "
        "marking duplicate handling complete in the readiness check.",
        "",
        f"- Preparation rows: {len(preparation):,}",
        f"- Unique source paths: {len(path_counts):,}",
        f"- Duplicate manifest-path groups: {len(duplicate_paths):,}",
        f"- Image files hashed: {len(images):,}",
        f"- Missing image paths: {len(missing):,}",
        f"- Hash read errors: {len(unreadable):,}",
        f"- Byte-identical SHA-256 groups: {len(identical_groups):,}",
        f"- Image files in byte-identical groups: "
        f"{sum(len(paths) for paths in identical_groups.values()):,}",
        f"- Additional byte-identical copies beyond one per group: "
        f"{sum(len(paths) - 1 for paths in identical_groups.values()):,}",
        f"- Duplicate basenames across paths: {len(basename_groups):,}",
        f"- Potential Roboflow filename-family groups: {len(family_groups):,}",
        f"- Images in potential Roboflow filename-family groups: "
        f"{sum(len(paths) for paths in family_groups.values()):,}",
        "",
        "## Duplicate manifest-path groups",
        "",
    ]
    if duplicate_paths:
        for relative, count in sorted(duplicate_paths.items()):
            lines.append(f"- `{relative}` — {count} rows")
    else:
        lines.append("None.")

    lines.extend(["", "## Byte-identical SHA-256 groups", ""])
    if identical_groups:
        for digest, paths in sorted(identical_groups.items()):
            lines.append(f"- SHA-256 `{digest}`")
            lines.extend(f"  - `{path}`" for path in sorted(paths))
    else:
        lines.append("None.")

    lines.extend(["", "## Duplicate basename groups", ""])
    if basename_groups:
        for basename, paths in sorted(basename_groups.items()):
            lines.append(f"- `{basename}`")
            lines.extend(f"  - `{path}`" for path in sorted(paths))
    else:
        lines.append("None.")

    lines.extend(["", "## Potential Roboflow augmentation-family groups", ""])
    if family_groups:
        for (source, family), paths in sorted(family_groups.items()):
            lines.append(f"- `{source}/{family}`")
            lines.extend(f"  - `{path}`" for path in sorted(paths))
    else:
        lines.append("None detected by the filename convention.")

    lines.extend(["", "## Missing files and hash errors", ""])
    lines.extend(f"- Missing: `{path}`" for path in missing)
    lines.extend(f"- Hash error: `{message}`" for message in unreadable)
    if not missing and not unreadable:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Recommended handling",
            "",
            "Review exact-hash groups first; keep one canonical image per physical "
            "specimen/capture in any later split, but preserve every original path "
            "in this review record. Check same-basename and filename-family groups "
            "against source metadata because different bytes can be augmented "
            "versions of one original. Do not automatically delete any image. "
            "Record the human resolution before using `--duplicates-reviewed` "
            "with the readiness command.",
            "",
        ]
    )
    DUPLICATE_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Hashed {len(images):,}; identical groups={len(identical_groups):,}; "
        f"path duplicates={len(duplicate_paths):,}; report={DUPLICATE_REPORT_PATH}"
    )


def write_readiness(
    *,
    min_per_class: int | None,
    duplicates_reviewed: bool,
) -> bool:
    preparation = read_csv(PREPARATION_PATH)
    decisions = load_decisions(DECISIONS_PATH)
    preparation_paths = {row["image_path"] for row in preparation}
    decisions_by_path = {row["image_path"]: row for row in decisions}
    approved = [
        row for row in decisions if row["review_status"] == "approved"
    ]
    approved_counts = Counter(row["verified_material"] for row in approved)

    checks: list[tuple[str, bool, str]] = []
    checks.append(
        ("At least one verified label exists", bool(approved), f"{len(approved):,} approved")
    )
    missing_approved_paths = [
        row["image_path"]
        for row in approved
        if row["image_path"] not in preparation_paths
        or not (
            (PROJECT_ROOT / row["image_path"]).resolve().is_relative_to(
                PROJECT_ROOT
            )
            and (PROJECT_ROOT / row["image_path"]).is_file()
        )
    ]
    checks.append(
        (
            "All approved images have valid paths",
            not missing_approved_paths,
            f"{len(missing_approved_paths):,} missing or invalid",
        )
    )

    duplicate_conflicts = len(decisions) - len(decisions_by_path)
    checks.append(
        (
            "No conflicting or duplicate decisions",
            duplicate_conflicts == 0,
            f"{duplicate_conflicts:,} duplicate paths",
        )
    )

    missing_fields = [
        row["image_path"]
        for row in decisions
        if not row["verified_material"].strip()
        or not row["reviewer_reason"].strip()
        or not row["reviewed_at"].strip()
        or (
            row["review_status"] == "approved"
            and (
                not row["evidence_reference"].strip()
                or row["evidence_reference"].strip().lower() == "none"
            )
        )
        or (
            row["verified_material"] == "Unknown"
            and row["unknown_outside_supported_confirmed"] != "yes"
        )
        or (
            row["verified_material"] in {"Steel", "Metal"}
            and row["evidence_reference"].strip().lower() == "none"
        )
    ]
    checks.append(
        (
            "No missing required review fields/evidence",
            not missing_fields,
            f"{len(missing_fields):,} incomplete decisions",
        )
    )

    present_classes = set(approved_counts) & set(APPROVED_MATERIALS)
    checks.append(
        (
            "All six material classes have verified examples",
            present_classes == set(APPROVED_MATERIALS),
            f"{len(present_classes)}/6 classes represented",
        )
    )
    if min_per_class is None:
        checks.append(
            (
                "Configured per-class sample threshold is met",
                False,
                "No threshold configured; no sample-size assumption made",
            )
        )
    else:
        below = {
            material: approved_counts[material]
            for material in APPROVED_MATERIALS
            if approved_counts[material] < min_per_class
        }
        checks.append(
            (
                "Configured per-class sample threshold is met",
                not below,
                (
                    f"minimum={min_per_class}; below threshold={below}"
                    if below
                    else f"minimum={min_per_class}; all classes meet it"
                ),
            )
        )

    checks.append(
        (
            "Unknown class is intentionally confirmed",
            all(
                row["unknown_outside_supported_confirmed"] == "yes"
                for row in approved
                if row["verified_material"] == "Unknown"
            )
            and bool(approved_counts["Unknown"]),
            f"{approved_counts['Unknown']:,} confirmed Unknown examples",
        )
    )
    steel_metal_ok = all(
        row["evidence_reference"].strip().lower() != "none"
        and row["reviewer_reason"].strip()
        for row in approved
        if row["verified_material"] in {"Steel", "Metal"}
    ) and bool(approved_counts["Steel"]) and bool(approved_counts["Metal"])
    checks.append(
        (
            "Steel/Metal distinction is documented for both classes",
            steel_metal_ok,
            (
                f"Steel={approved_counts['Steel']}; Metal={approved_counts['Metal']}"
            ),
        )
    )
    checks.append(
        (
            "Duplicate handling is complete",
            duplicates_reviewed,
            (
                "Human attestation supplied"
                if duplicates_reviewed
                else "Review DUPLICATE_REVIEW_REPORT.md and rerun with --duplicates-reviewed"
            ),
        )
    )

    ready = all(passed for _, passed, _ in checks)
    lines = [
        "# Training readiness check",
        "",
        "**READY FOR TRAINING**" if ready else "**NOT READY FOR TRAINING**",
        "",
        "This checker does not train or modify models. The sample threshold is "
        + (
            f"explicitly configured at {min_per_class} approved images per class."
            if min_per_class is not None
            else "not configured; the checker does not guess a threshold."
        ),
        "",
        "| Check | Result | Details |",
        "|---|---|---|",
    ]
    for name, passed, details in checks:
        result = "PASS" if passed else "FAIL"
        lines.append(f"| {name} | {result} | {details} |")
    lines.extend(
        [
            "",
            "## Approved counts",
            "",
            "| Class | Count |",
            "|---|---:|",
        ]
    )
    for material in APPROVED_MATERIALS:
        lines.append(f"| {material} | {approved_counts[material]} |")
    lines.extend(
        [
            "",
            "A passing result is a preparation gate only. It does not authorize "
            "training or integration.",
            "",
        ]
    )
    READINESS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"{'READY' if ready else 'NOT READY'} FOR TRAINING")
    for name, passed, details in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {name}: {details}")
    print(f"Report: {READINESS_PATH}")
    return ready


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit duplicates, progress, and readiness without training."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("duplicates", help="Hash source images and write duplicate report.")
    subparsers.add_parser("progress", help="Regenerate human-review progress.")
    readiness = subparsers.add_parser(
        "readiness", help="Check data readiness; never trains a model."
    )
    readiness.add_argument(
        "--min-per-class",
        type=int,
        help="Reviewer-configured minimum approved images required in each class.",
    )
    readiness.add_argument(
        "--duplicates-reviewed",
        action="store_true",
        help="Attest that duplicate groups were reviewed and resolved by a human.",
    )
    args = parser.parse_args()

    try:
        if args.command == "duplicates":
            write_duplicate_report()
        elif args.command == "progress":
            summary = write_progress()
            print(
                f"Reviewed {summary['reviewed']:,}/{summary['total']:,}; "
                f"report={PROGRESS_PATH}"
            )
        else:
            if args.min_per_class is not None and args.min_per_class < 1:
                parser.error("--min-per-class must be a positive integer.")
            write_progress()
            ready = write_readiness(
                min_per_class=args.min_per_class,
                duplicates_reviewed=args.duplicates_reviewed,
            )
            if not ready:
                raise SystemExit(1)
    except (OSError, csv.Error, DecisionValidationError) as error:
        raise SystemExit(f"Audit failed: {error}") from error


if __name__ == "__main__":
    main()
