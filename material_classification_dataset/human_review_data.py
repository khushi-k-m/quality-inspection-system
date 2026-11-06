from __future__ import annotations

import csv
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = Path(__file__).resolve().parent
PREPARATION_PATH = DATASET_DIR / "human_review_preparation.csv"
DEFAULT_DECISIONS_PATH = DATASET_DIR / "human_review_decisions.csv"
DECISIONS_PATH = Path(
    os.environ.get("HUMAN_REVIEW_DECISIONS_PATH", DEFAULT_DECISIONS_PATH)
).resolve()

MATERIAL_DECISIONS = (
    "Steel",
    "Metal",
    "Fabric",
    "PCB",
    "Welding",
    "Unknown",
    "Unusable",
    "Needs Review",
)
APPROVED_MATERIALS = MATERIAL_DECISIONS[:6]
CSV_FIELDS = (
    "image_path",
    "verified_material",
    "review_status",
    "evidence_reference",
    "reviewer_reason",
    "reviewed_at",
    "reviewer",
    "source_dataset",
    "source_annotation_path",
    "original_candidate_material",
    "openclip_signal",
    "unknown_outside_supported_confirmed",
    "steel_metal_unresolved",
)


class DecisionValidationError(ValueError):
    pass


def read_csv(path: Path, *, missing_ok: bool = False) -> list[dict[str, str]]:
    if missing_ok and not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def load_decisions(path: Path = DECISIONS_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing_columns = set(CSV_FIELDS) - set(reader.fieldnames or ())
        if missing_columns:
            raise DecisionValidationError(
                "Decision file is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
        rows = [
            {field: row.get(field) or "" for field in CSV_FIELDS}
            for row in reader
        ]
    seen: set[str] = set()
    for row in rows:
        image_path = row.get("image_path", "").strip()
        if not image_path:
            raise DecisionValidationError("A saved decision has no image_path.")
        if image_path in seen:
            raise DecisionValidationError(
                f"Conflicting duplicate decisions exist for {image_path}."
            )
        seen.add(image_path)
        expected_status = (
            "approved"
            if row["verified_material"] in APPROVED_MATERIALS
            else "rejected"
            if row["verified_material"] == "Unusable"
            else "needs_review"
            if row["verified_material"] == "Needs Review"
            else ""
        )
        if not expected_status or row.get("review_status") != expected_status:
            raise DecisionValidationError(
                f"Saved decision has an invalid material/status combination for "
                f"{image_path}."
            )
    return rows


def write_decisions(
    rows: list[dict[str, str]], path: Path = DECISIONS_PATH
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}_", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(handle, "w", newline="", encoding="utf-8-sig") as output:
            writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def make_decision(
    candidate: dict[str, str],
    material: str,
    evidence_reference: str,
    reviewer_reason: str,
    *,
    reviewer: str = "",
    unknown_confirmed: bool = False,
    unusable_confirmed: bool = False,
    steel_metal_unresolved: bool = False,
) -> dict[str, str]:
    if material not in MATERIAL_DECISIONS:
        raise DecisionValidationError("Select one of the available review decisions.")
    if not reviewer_reason.strip():
        raise DecisionValidationError("Enter a reviewer rationale.")

    evidence = evidence_reference.strip()
    if material in APPROVED_MATERIALS and not evidence:
        raise DecisionValidationError(
            "Approved material decisions require an evidence reference or 'none'."
        )
    if material in {"Steel", "Metal"} and evidence.lower() == "none":
        raise DecisionValidationError(
            "Steel and Metal require traceable evidence distinguishing steel "
            "from non-steel metal; visual appearance alone is insufficient."
        )
    if material == "Unknown" and not unknown_confirmed:
        raise DecisionValidationError(
            "Confirm that the visible material is outside all supported classes."
        )
    if material == "Unusable" and not unusable_confirmed:
        raise DecisionValidationError("Confirm the Unusable decision explicitly.")

    source_relative = candidate.get("image_path", "").strip()
    source = (PROJECT_ROOT / source_relative).resolve()
    if (
        not source_relative
        or not source.is_relative_to(PROJECT_ROOT)
        or not source.is_file()
    ):
        raise DecisionValidationError(
            "The original image path is missing or outside the project."
        )

    status = (
        "approved"
        if material in APPROVED_MATERIALS
        else "rejected"
        if material == "Unusable"
        else "needs_review"
    )
    return {
        "image_path": source_relative,
        "verified_material": material,
        "review_status": status,
        "evidence_reference": evidence or "none",
        "reviewer_reason": reviewer_reason.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reviewer": reviewer.strip(),
        "source_dataset": candidate.get("source_dataset", ""),
        "source_annotation_path": candidate.get("source_annotation_path", ""),
        "original_candidate_material": candidate.get(
            "proposed_material_candidate", ""
        ),
        "openclip_signal": candidate.get(
            "openclip_screening_signal_unverified", ""
        ),
        "unknown_outside_supported_confirmed": (
            "yes" if material == "Unknown" and unknown_confirmed else "no"
        ),
        "steel_metal_unresolved": (
            "yes"
            if material == "Needs Review" and steel_metal_unresolved
            else "no"
        ),
    }


def save_decision(
    candidate: dict[str, str],
    material: str,
    evidence_reference: str,
    reviewer_reason: str,
    *,
    reviewer: str = "",
    unknown_confirmed: bool = False,
    unusable_confirmed: bool = False,
    steel_metal_unresolved: bool = False,
    path: Path = DECISIONS_PATH,
) -> list[dict[str, str]]:
    record = make_decision(
        candidate,
        material,
        evidence_reference,
        reviewer_reason,
        reviewer=reviewer,
        unknown_confirmed=unknown_confirmed,
        unusable_confirmed=unusable_confirmed,
        steel_metal_unresolved=steel_metal_unresolved,
    )
    rows = load_decisions(path)
    updated = False
    for index, existing in enumerate(rows):
        if existing["image_path"] == record["image_path"]:
            rows[index] = record
            updated = True
            break
    if not updated:
        rows.append(record)
    write_decisions(rows, path)
    return rows


def summarize_decisions(
    preparation: list[dict[str, str]], decisions: list[dict[str, str]]
) -> dict[str, object]:
    if len({row["image_path"] for row in preparation}) != len(preparation):
        raise DecisionValidationError("Preparation manifest has duplicate paths.")
    decision_by_path = {row["image_path"]: row for row in decisions}
    unknown_paths = set(decision_by_path) - {
        row["image_path"] for row in preparation
    }
    if unknown_paths:
        raise DecisionValidationError(
            f"Saved decisions refer to {len(unknown_paths)} images outside the "
            "preparation manifest."
        )
    status_counts = Counter(row["review_status"] for row in decisions)
    material_counts = Counter(
        row["verified_material"]
        for row in decisions
        if row["review_status"] == "approved"
    )
    no_evidence = [
        row
        for row in decisions
        if row["review_status"] == "approved"
        and row["evidence_reference"].strip().lower() == "none"
    ]
    additional_verification = [
        row
        for row in decisions
        if row["review_status"] != "approved"
        or row["evidence_reference"].strip().lower() == "none"
        or not row["reviewer_reason"].strip()
    ]
    steel_metal_unresolved = [
        row
        for row in decisions
        if row["verified_material"] == "Needs Review"
        and row.get("steel_metal_unresolved") == "yes"
    ]
    return {
        "total": len(preparation),
        "reviewed": len(decisions),
        "not_reviewed": len(preparation) - len(decisions),
        "status_counts": status_counts,
        "material_counts": material_counts,
        "evidence_reference_count": sum(
            row["review_status"] == "approved"
            and bool(row["evidence_reference"].strip())
            and row["evidence_reference"].strip().lower() != "none"
            for row in decisions
        ),
        "no_evidence_count": len(no_evidence),
        "additional_verification_count": len(additional_verification),
        "steel_metal_unresolved_count": len(steel_metal_unresolved),
    }
