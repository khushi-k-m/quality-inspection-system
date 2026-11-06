import csv
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = Path(__file__).resolve().parent
SOURCE_MANIFEST = DATASET_DIR / "ai_screening_manifest.csv"
SCREENING_MANIFEST = DATASET_DIR / "candidate_visual_screening.csv"
REVIEW_MANIFEST = DATASET_DIR / "review_manifest.csv"
OUTPUT_CSV = DATASET_DIR / "human_review_preparation.csv"
REPORT_PATH = DATASET_DIR / "HUMAN_REVIEW_PREPARATION_REPORT.md"

# These are collection-level hypotheses supported by local source documentation,
# never verified image labels. A generic metal-surface pool cannot distinguish
# steel from non-steel metal and therefore has no proposed class.
SOURCE_EVIDENCE = {
    "dataset": {
        "candidate": "steel",
        "source": (
            "README.dataset.txt identifies the upstream collection as "
            "severstal-steel-defect-detection; README.roboflow.txt describes "
            "steel-defect annotations. The names describe collection intent, "
            "not independently verified material for each image."
        ),
        "reference": (
            "dataset/README.dataset.txt; dataset/README.roboflow.txt; "
            "https://universe.roboflow.com/daniil-khoroshev-pmi-gmail-com/"
            "severstal-steel-defect-detection"
        ),
        "reliability": "medium_collection_level_candidate_only",
    },
    "dataset_metal": {
        "candidate": "metal_unspecified",
        "source": (
            "README.dataset.txt and README.roboflow.txt describe a metal-surface "
            "defect collection. Neither document identifies steel versus "
            "non-steel for individual images."
        ),
        "reference": (
            "dataset_metal/README.dataset.txt; "
            "dataset_metal/README.roboflow.txt; "
            "https://universe.roboflow.com/repository/"
            "defect-detection-metal-surface/dataset/3"
        ),
        "reliability": "low_collection_level_candidate_only",
    },
    "dataset_fabric": {
        "candidate": "fabric",
        "source": (
            "README.dataset.txt and data.yaml identify a fabric-defect "
            "collection and list color bleeding, crease, and hole defect classes. "
            "These are source-level task descriptions, not per-image material "
            "verification."
        ),
        "reference": (
            "dataset_fabric/README.dataset.txt; dataset_fabric/data.yaml; "
            "https://universe.roboflow.com/fabric-defects-dataset/"
            "fabric-defect-detection-ipvbu/dataset/18"
        ),
        "reliability": "medium_collection_level_candidate_only",
    },
    "dataset_pcb_boards": {
        "candidate": "pcb",
        "source": (
            "README.dataset.txt identifies a PCB defect-detection collection; "
            "data.yaml lists PCB-specific defect names (missing_hole, mouse_bite, "
            "open_circuit, short, spur, spurious_copper). Source-level context "
            "supports PCB review candidates but does not verify each image."
        ),
        "reference": (
            "dataset_pcb_boards/README.dataset.txt; "
            "dataset_pcb_boards/data.yaml; "
            "https://universe.roboflow.com/michalek/"
            "pcb-defect-detection-kckiu-mj0m9/dataset/1"
        ),
        "reliability": "high_collection_level_candidate_only",
    },
    "dataset_welding": {
        "candidate": "welding",
        "source": (
            "README.dataset.txt and README.roboflow.txt describe a welding "
            "defect-detection collection and weld annotations. This supports "
            "candidate review, not individual confirmation of a weld or its "
            "substrate."
        ),
        "reference": (
            "dataset_welding/README.dataset.txt; "
            "dataset_welding/README.roboflow.txt; "
            "https://universe.roboflow.com/wdd-mpjs1/"
            "welding-defect-detection-a3jqd/dataset/4"
        ),
        "reliability": "high_collection_level_candidate_only",
    },
    "dataset_wood_surface": {
        "candidate": "unknown_wood",
        "source": (
            "README.dataset.txt documents planed European beech board surfaces; "
            "data.yaml and README.roboflow.txt identify wood-defect annotations. "
            "Wood is an unsupported-material candidate for unknown, but the "
            "source description alone does not verify each image."
        ),
        "reference": (
            "dataset_wood_surface/README.dataset.txt; "
            "dataset_wood_surface/data.yaml; "
            "https://universe.roboflow.com/yolo11-yqwwf/"
            "wood-defect-detection-dataset-w0ws3/dataset/1"
        ),
        "reliability": "high_collection_level_candidate_only",
    },
}

FIELDS = [
    "image_path",
    "source_dataset",
    "source_annotation_path",
    "source_annotation_status",
    "proposed_material_candidate",
    "material_evidence_status",
    "evidence_source",
    "evidence_reference",
    "evidence_reliability",
    "human_review_required",
    "review_queue",
    "existing_review_status",
    "existing_review_class_unverified",
    "existing_review_reason",
    "existing_evidence_reference",
    "openclip_screening_flag_unverified",
    "openclip_screening_signal_unverified",
    "is_verified_label",
    "is_evidence_supported_candidate",
    "is_ambiguous_flag",
    "is_possible_unusable_flag",
    "is_unknown_class_candidate",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def main() -> None:
    source_rows = read_csv(SOURCE_MANIFEST)
    screening_rows = read_csv(SCREENING_MANIFEST)
    existing_reviews = read_csv(REVIEW_MANIFEST)

    screening_by_path = {row["image_path"]: row for row in screening_rows}
    reviews_by_path = {row["image_path"]: row for row in existing_reviews}
    if len(screening_by_path) != len(screening_rows):
        raise ValueError("Screening manifest contains duplicate image paths.")
    if len(reviews_by_path) != len(existing_reviews):
        raise ValueError("Review manifest contains duplicate image paths.")

    records = []
    for source_row in source_rows:
        image_path = source_row["image_path"]
        if image_path in screening_by_path:
            screening = screening_by_path.pop(image_path)
        else:
            raise ValueError(f"Missing screening row for {image_path}")
        review = reviews_by_path.get(image_path, {})
        source_name = source_row["source_dataset"]
        evidence = SOURCE_EVIDENCE.get(source_name)

        source_image = PROJECT_ROOT / Path(image_path)
        if not source_image.is_file():
            raise FileNotFoundError(f"Source image is missing: {image_path}")

        annotation = source_image.parent.parent / "labels" / (
            source_image.stem + ".txt"
        )
        annotation_status = (
            "present_nonempty"
            if annotation.is_file() and annotation.stat().st_size > 0
            else "present_empty"
            if annotation.is_file()
            else "not_found"
        )
        if annotation_status == "not_found":
            annotation_reference = ""
        else:
            annotation_reference = relative_path(annotation)

        screening_flag = screening["proposed_material_class"]
        review_queue = {
            "reject_unusable": "possible_unusable_review_flag",
            "ambiguous": "ambiguous_screening_flag",
        }.get(screening_flag, "source_candidate_review")
        if review.get("review_status") == "needs_review":
            review_queue = "existing_needs_review_decision"

        candidate = evidence["candidate"] if evidence else "unresolved"
        evidence_reference = evidence["reference"] if evidence else ""
        evidence_source = evidence["source"] if evidence else (
            "No source-level material documentation was matched."
        )
        reliability = evidence["reliability"] if evidence else "none"

        records.append(
            {
                "image_path": image_path,
                "source_dataset": source_name,
                "source_annotation_path": annotation_reference,
                "source_annotation_status": annotation_status,
                "proposed_material_candidate": candidate,
                "material_evidence_status": (
                    "collection_level_candidate_only"
                    if evidence
                    else "no_supporting_source_evidence"
                ),
                "evidence_source": evidence_source,
                "evidence_reference": evidence_reference,
                "evidence_reliability": reliability,
                "human_review_required": "yes",
                "review_queue": review_queue,
                "existing_review_status": review.get("review_status", ""),
                "existing_review_class_unverified": review.get(
                    "material_class", ""
                ),
                "existing_review_reason": review.get("review_reason", ""),
                "existing_evidence_reference": review.get(
                    "evidence_reference", ""
                ),
                "openclip_screening_flag_unverified": screening_flag,
                "openclip_screening_signal_unverified": screening.get(
                    "screening_signal", ""
                ),
                "is_verified_label": "no",
                "is_evidence_supported_candidate": "yes" if evidence else "no",
                "is_ambiguous_flag": (
                    "yes" if screening_flag == "ambiguous" else "no"
                ),
                "is_possible_unusable_flag": (
                    "yes" if screening_flag == "reject_unusable" else "no"
                ),
                "is_unknown_class_candidate": (
                    "yes" if candidate == "unknown_wood" else "no"
                ),
            }
        )

    if screening_by_path:
        raise ValueError(
            f"{len(screening_by_path)} screening rows have no source-manifest row."
        )

    output_paths = {row["image_path"] for row in records}
    if len(output_paths) != len(records):
        raise ValueError("Source manifest contains duplicate image paths.")

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(records)

    queue_counts = Counter(row["review_queue"] for row in records)
    source_counts = Counter(row["source_dataset"] for row in records)
    candidate_counts = Counter(
        row["proposed_material_candidate"] for row in records
    )
    flag_counts = Counter(
        row["openclip_screening_flag_unverified"] for row in records
    )
    annotation_counts = Counter(
        row["source_annotation_status"] for row in records
    )
    evidence_rows = sum(bool(row["evidence_reference"]) for row in records)
    item_evidence_rows = sum(
        bool(row["existing_evidence_reference"]) for row in records
    )
    existing_needs_review = sum(
        row["existing_review_status"] == "needs_review" for row in records
    )

    report = [
        "# Human-review preparation audit",
        "",
        "This is a review-preparation artifact only. It is not a labeled training "
        "dataset. No images were copied, moved, edited, rejected, or approved; no "
        "model was trained. Existing review decisions are carried through unchanged.",
        "",
        "## Scope and evidence standard",
        "",
        f"- Unique source images in the output: **{len(records):,}**.",
        "- Local source documentation and source URLs establish collection-level "
        "candidate context only. Folder names, filenames, YOLO defect classes, "
        "empty/nonempty annotations, dataset provenance, and OpenCLIP results do "
        "not establish an image-level material label.",
        "- YOLO annotation paths are recorded for traceability. Their defect "
        "annotations provide no independent material confirmation by themselves.",
        "- OpenCLIP values and flags are copied only as unverified screening "
        "signals; they do not decide class, usability, or approval.",
        "- `metal_unspecified` means metal-versus-steel identity remains unresolved. "
        "It is not an assigned non-steel `metal` label.",
        "- `unknown_wood` is a collection-level candidate for review as an "
        "unsupported material, not a verified `unknown` label.",
        "- Every image remains subject to human review. Queue labels are flags, "
        "not disposition decisions; possible-unusable rows were not rejected.",
        "",
        "## Verified labels",
        "",
        "| Material class | Verified images |",
        "|---|---:|",
    ]
    for label in ("steel", "metal", "fabric", "pcb", "welding", "unknown"):
        report.append(f"| {label} | 0 |")

    report.extend(
        [
            "",
            "## Source-supported candidate counts (not verified labels)",
            "",
            "| Candidate | Images | Evidence reliability |",
            "|---|---:|---|",
        ]
    )
    reliability_by_candidate = {}
    for row in records:
        reliability_by_candidate[row["proposed_material_candidate"]] = row[
            "evidence_reliability"
        ]
    for label in (
        "steel",
        "metal_unspecified",
        "fabric",
        "pcb",
        "welding",
        "unknown_wood",
        "unresolved",
    ):
        report.append(
            f"| {label} | {candidate_counts[label]:,} | "
            f"{reliability_by_candidate.get(label, 'none')} |"
        )

    report.extend(
        [
            "",
            "## Review queues and screening flags",
            "",
            "The primary `review_queue` is exclusive (existing review decision "
            "takes priority, then possible-unusable flag, then ambiguous flag). "
            "Source-candidate classes and OpenCLIP flags are separately recorded "
            "per image and can overlap this queue.",
            "",
            "| Queue | Images |",
            "|---|---:|",
        ]
    )
    for queue in (
        "existing_needs_review_decision",
        "possible_unusable_review_flag",
        "ambiguous_screening_flag",
        "source_candidate_review",
    ):
        report.append(f"| {queue} | {queue_counts[queue]:,} |")
    report.extend(
        [
            "",
            "| OpenCLIP screening signal (unverified) | Images |",
            "|---|---:|",
        ]
    )
    for label, count in sorted(flag_counts.items()):
        report.append(f"| {label} | {count:,} |")

    report.extend(
        [
            "",
            "## Evidence-reference counts",
            "",
            f"- Rows with a traceable collection-level local-document/source-URL "
            f"reference: **{evidence_rows:,}**.",
            f"- Rows with independent, image-specific material-evidence "
            f"references: **{item_evidence_rows:,}**.",
            f"- Existing review-manifest needs-review rows preserved: "
            f"**{existing_needs_review:,}**; their evidence references remain "
            "blank.",
            "",
            "## Source-pool audit",
            "",
            "| Source manifest pool | Images | Collection-level candidate | "
            "Annotation files |",
            "|---|---:|---|---:|",
        ]
    )
    for source_name in SOURCE_EVIDENCE:
        source_rows_for_pool = [
            row for row in records if row["source_dataset"] == source_name
        ]
        source_annotation_count = sum(
            row["source_annotation_status"] != "not_found"
            for row in source_rows_for_pool
        )
        report.append(
            f"| {source_name} | {source_counts[source_name]:,} | "
            f"{SOURCE_EVIDENCE[source_name]['candidate']} | "
            f"{source_annotation_count:,} |"
        )
    report.extend(
        [
            "",
            "Annotation-file status totals: "
            + "; ".join(
                f"{status}={annotation_counts[status]:,}"
                for status in sorted(annotation_counts)
            )
            + ".",
            "",
            "## Training readiness",
            "",
            "There are **0 verified image-level examples in every requested "
            "class**. There is not enough verified data to train a six-class "
            "classifier. First, humans must review each retained source image "
            "without relying on its directory name, filename, defect class, or "
            "OpenCLIP result; record an image-specific evidence source/reference "
            "and rationale for every proposed label. Steel and non-steel metal "
            "require traceable part/specimen/material documentation that resolves "
            "the distinction. Confirm fabric, PCB, and welding from the visible "
            "item or trustworthy item-specific records. Confirm `unknown` images "
            "are outside all five supported classes. Review possible-unusable "
            "images individually before excluding any. Resolve whether welding "
            "is a material class or an overlapping process label, then deduplicate "
            "physical items/capture sessions and build leakage-safe splits only "
            "after labels are verified.",
            "",
            f"Preparation manifest: `{OUTPUT_CSV.name}`.",
        ]
    )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Prepared {len(records)} unique source-image rows")
    print(f"Output manifest: {OUTPUT_CSV}")
    print(f"Audit report: {REPORT_PATH}")
    print(f"Queue counts: {dict(queue_counts)}")
    print(f"Candidate counts: {dict(candidate_counts)}")
    print(f"Screening flag counts: {dict(flag_counts)}")
    print(f"Traceable source references: {evidence_rows}")
    print(f"Image-specific evidence references: {item_evidence_rows}")


if __name__ == "__main__":
    main()
