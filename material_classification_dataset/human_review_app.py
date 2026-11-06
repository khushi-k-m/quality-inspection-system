from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from human_review_data import (
    APPROVED_MATERIALS,
    DATASET_DIR,
    DECISIONS_PATH,
    MATERIAL_DECISIONS,
    PREPARATION_PATH,
    PROJECT_ROOT,
    DecisionValidationError,
    load_decisions,
    read_csv,
    save_decision,
    summarize_decisions,
)

DUPLICATE_REPORT_PATH = DATASET_DIR / "DUPLICATE_REVIEW_REPORT.md"
DECISION_FILTERS = (
    "all",
    "needs review",
    "reviewed",
    "Steel",
    "Metal",
    "Fabric",
    "PCB",
    "Welding",
    "Unknown",
    "Unusable",
)

st.set_page_config(page_title="Material Dataset Human Review", layout="wide")
st.title("Material Dataset Human Review")
st.warning(
    "Make decisions from the actual image and traceable item-specific evidence. "
    "OpenCLIP, source folders, filenames, dataset documentation, and YOLO defect "
    "annotations are not image-level ground truth. Steel and Metal require "
    "evidence distinguishing steel from non-steel metal."
)
st.caption(
    "One original image at a time. Decisions are saved separately in "
    "`human_review_decisions.csv`; source images and existing manifests are never changed."
)
if not DUPLICATE_REPORT_PATH.is_file():
    st.error(
        "Duplicate screening has not been run. Run "
        "`audit_human_review.py duplicates` before starting review."
    )
    st.stop()
if DUPLICATE_REPORT_PATH.stat().st_mtime < PREPARATION_PATH.stat().st_mtime:
    st.error(
        "The duplicate report is older than the preparation manifest. "
        "Regenerate it with `audit_human_review.py duplicates` before reviewing."
    )
    st.stop()
duplicate_summary = {}
with DUPLICATE_REPORT_PATH.open(encoding="utf-8") as duplicate_report:
    for line in duplicate_report:
        if line.startswith("- Byte-identical SHA-256 groups:"):
            duplicate_summary["identical"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Potential Roboflow filename-family groups:"):
            duplicate_summary["families"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Handling status:**"):
            duplicate_summary["handling"] = line.split("**", 2)[2].strip()
        if len(duplicate_summary) == 3:
            break
if duplicate_summary.get("identical") or duplicate_summary.get("families"):
    st.info(
        "Duplicate audit completed before review: "
        f"{duplicate_summary.get('identical', 'unknown')} byte-identical groups; "
        f"{duplicate_summary.get('families', 'unknown')} potential filename families. "
        f"{duplicate_summary.get('handling', 'Human review is still required.')}"
    )


def annotation_lines(relative_path: str) -> list[str]:
    if not relative_path:
        return []
    path = (PROJECT_ROOT / relative_path).resolve()
    if not path.is_relative_to(PROJECT_ROOT) or not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


try:
    candidates = read_csv(PREPARATION_PATH)
    decisions = load_decisions()
    stats = summarize_decisions(candidates, decisions)
except (OSError, csv.Error, DecisionValidationError) as error:
    st.error(f"Could not load review data safely: {error}")
    st.stop()

decision_by_path = {row["image_path"]: row for row in decisions}
status_counts = stats["status_counts"]
metrics = st.columns(4)
metrics[0].metric("Reviewed", f"{stats['reviewed']:,} / {stats['total']:,}")
metrics[1].metric("Approved", status_counts["approved"])
metrics[2].metric("Needs Review", status_counts["needs_review"])
metrics[3].metric("Rejected", status_counts["rejected"])

filter_column, search_column = st.columns([1, 3])
with filter_column:
    selected_filter = st.selectbox("Filter", DECISION_FILTERS, key="review_filter")
with search_column:
    search_text = st.text_input(
        "Search image path or source dataset", key="review_search"
    ).strip().casefold()

filtered = []
for row in candidates:
    prior = decision_by_path.get(row["image_path"])
    status = prior["review_status"] if prior else "needs_review"
    material = prior["verified_material"] if prior else ""
    if selected_filter == "needs review" and status != "needs_review":
        continue
    if selected_filter == "reviewed" and prior is None:
        continue
    if selected_filter in APPROVED_MATERIALS and material != selected_filter:
        continue
    if selected_filter == "Unusable" and material != "Unusable":
        continue
    if search_text and search_text not in (
        row["image_path"] + " " + row["source_dataset"]
    ).casefold():
        continue
    filtered.append(row)

signature = (selected_filter, search_text)
if st.session_state.get("filter_signature") != signature:
    st.session_state.filter_signature = signature
    st.session_state.review_index = 0

if not filtered:
    st.info("No images match this filter.")
    st.stop()

index = min(max(int(st.session_state.get("review_index", 0)), 0), len(filtered) - 1)
candidate = filtered[index]
image_path = candidate["image_path"]
decision_key = hashlib.sha256(image_path.encode("utf-8")).hexdigest()[:16]
existing = decision_by_path.get(image_path, {})

previous_column, position_column, next_column = st.columns([1, 4, 1])
with previous_column:
    if st.button("Previous", disabled=index == 0, use_container_width=True):
        st.session_state.review_index = index - 1
        st.rerun()
with position_column:
    st.progress((index + 1) / len(filtered))
    st.caption(f"Image {index + 1:,} / {len(filtered):,} in current filter")
with next_column:
    if st.button(
        "Next",
        disabled=index >= len(filtered) - 1,
        use_container_width=True,
    ):
        st.session_state.review_index = index + 1
        st.rerun()

image_column, review_column = st.columns([1.25, 1])
source_path = (PROJECT_ROOT / image_path).resolve()
preview = None
image_problem = ""
width = height = 0
file_type = source_path.suffix.lstrip(".").upper()
try:
    if not source_path.is_relative_to(PROJECT_ROOT) or not source_path.is_file():
        raise OSError("Image path is missing or outside the project.")
    with Image.open(source_path) as opened:
        width, height = opened.size
        file_type = opened.format or file_type
        preview = ImageOps.exif_transpose(opened).convert("RGB")
except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
    image_problem = str(error)

with image_column:
    st.subheader("Source image")
    if preview is not None:
        st.image(preview, use_container_width=True)
        st.caption(f"{width} × {height} | {file_type}")
    else:
        st.error(
            "The image could not be opened. This is only a warning; a human must "
            f"confirm whether it is Unusable. Details: {image_problem}"
        )
        st.caption(f"Dimensions: unknown | file extension: {file_type or 'unknown'}")

with review_column:
    st.subheader("Human decision")
    current_status = (
        existing.get("review_status")
        or candidate.get("existing_review_status")
        or "needs_review"
    )
    st.caption(f"Current review status: **{current_status}**")
    prior_material = existing.get("verified_material", "")
    available_decisions = (
        ("Unusable", "Needs Review")
        if image_problem
        else MATERIAL_DECISIONS
    )
    decision_options = ("Select a decision", *available_decisions)
    default_decision = (
        prior_material
        if prior_material in available_decisions
        else "Select a decision"
    )
    with st.form(f"review_form_{decision_key}"):
        selected_decision = st.selectbox(
            "Material decision",
            decision_options,
            index=decision_options.index(default_decision),
            help="No decision is inferred from the candidate, source, annotation, or model signal.",
        )
        evidence_reference = st.text_input(
            "Evidence reference (required for approved labels)",
            value=existing.get("evidence_reference", ""),
            help=(
                "Enter an actual traceable record or URL. If none exists, type "
                "'none'; the rationale is still required. Steel and Metal cannot "
                "be approved with 'none'."
            ),
        )
        reviewer_reason = st.text_area(
            "Reviewer rationale (required)",
            value=existing.get("reviewer_reason", ""),
            height=110,
        )
        reviewer = st.text_input("Reviewer (optional)", value=existing.get("reviewer", ""))
        unknown_confirmed = False
        if selected_decision == "Unknown":
            unknown_confirmed = st.checkbox(
                "I confirm the visible item is outside all supported classes.",
                value=(
                    existing.get("unknown_outside_supported_confirmed") == "yes"
                ),
            )
        steel_metal_unresolved = False
        if selected_decision == "Needs Review":
            steel_metal_unresolved = st.checkbox(
                "This case is unresolved specifically because Steel vs. Metal identity is uncertain.",
                value=existing.get("steel_metal_unresolved") == "yes",
            )
        unusable_confirmed = False
        if selected_decision == "Unusable":
            unusable_confirmed = st.checkbox(
                "I reviewed and intentionally confirm this image is unusable.",
                value=prior_material == "Unusable",
            )
        st.caption(
            "Steel/Metal require traceable evidence resolving steel vs. non-steel. "
            "A reviewer may choose Needs Review when identity or image quality is uncertain."
        )
        save_clicked = st.form_submit_button("Save decision", type="primary")
        if save_clicked:
            if selected_decision == "Select a decision":
                st.error("Select one of the eight decisions.")
            elif selected_decision == "Unusable" and not unusable_confirmed:
                st.error("Confirm the Unusable decision explicitly.")
            else:
                try:
                    save_decision(
                        candidate,
                        selected_decision,
                        evidence_reference,
                        reviewer_reason,
                        reviewer=reviewer,
                        unknown_confirmed=unknown_confirmed,
                        unusable_confirmed=unusable_confirmed,
                        steel_metal_unresolved=steel_metal_unresolved,
                    )
                    st.success(
                        "Decision saved. Revisiting this image updates its existing row."
                    )
                    st.rerun()
                except (DecisionValidationError, OSError, csv.Error) as error:
                    st.error(f"Decision was not saved: {error}")

    if st.button("Skip", key=f"skip_{decision_key}"):
        st.session_state.review_index = min(index + 1, len(filtered) - 1)
        st.rerun()

with st.expander("Source and screening information"):
    st.write(f"**Image path:** `{image_path}`")
    st.write(f"**Source dataset:** `{candidate['source_dataset']}`")
    st.write(
        f"**Source annotation:** `{candidate['source_annotation_path'] or 'not found'}` "
        f"({candidate['source_annotation_status']})"
    )
    st.caption(
        "YOLO annotations describe defects, not material. Annotation class IDs "
        "must not be used as material labels."
    )
    lines = annotation_lines(candidate["source_annotation_path"])
    if lines:
        st.code("\n".join(lines[:20]) or "(empty annotation file)")
    st.write(
        f"**Source documentation:** {candidate['evidence_reference'] or 'No reference recorded'}"
    )
    st.write(
        f"**Collection-level candidate:** {candidate['proposed_material_candidate']} "
        f"({candidate['evidence_reliability']})"
    )
    st.write(
        f"**OpenCLIP flag (unverified):** "
        f"{candidate['openclip_screening_flag_unverified']}"
    )
    st.code(candidate["openclip_screening_signal_unverified"] or "No screening signal")
    if candidate.get("existing_review_status"):
        st.info(
            "Prior review_manifest.csv entry is shown for context only and is not "
            "modified by this tool."
        )
        st.json(
            {
                "status": candidate["existing_review_status"],
                "class_unverified": candidate["existing_review_class_unverified"],
                "reason": candidate["existing_review_reason"],
                "evidence_reference": candidate["existing_evidence_reference"],
            }
        )

st.caption(
    f"Resumable decisions: {DECISIONS_PATH}"
)
