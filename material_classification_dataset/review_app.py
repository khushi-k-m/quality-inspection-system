from __future__ import annotations

import csv
import hashlib
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

REVIEW_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = REVIEW_ROOT.parent
BATCH_PATH = REVIEW_ROOT / "review_batch.csv"
MANIFEST_PATH = REVIEW_ROOT / "review_manifest.csv"
FIELDS = ("image_path", "material_class", "source_dataset", "review_status", "review_reason")
CLASSES = ("steel", "metal", "fabric", "pcb", "welding", "unknown")
DECISIONS = (*CLASSES, "reject", "needs_review")

st.set_page_config(page_title="Material Image Review", layout="wide")
st.title("Material Image Review")
st.caption("Review the image, not its dataset name or filename. Candidate labels are blank until you decide.")
st.warning(
    "Steel and metal overlap, and welding is a process/joint rather than a material. "
    "For steel or metal, visual appearance alone is not material verification; use real specimen evidence. "
    "Resolve the class definitions before approving overlapping cases."
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def write_manifest(rows: list[dict[str, str]]) -> None:
    handle, temporary_name = tempfile.mkstemp(prefix="review_manifest_", suffix=".csv", dir=REVIEW_ROOT)
    try:
        with os.fdopen(handle, "w", newline="", encoding="utf-8-sig") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, MANIFEST_PATH)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_source_path(relative_path: str) -> Path:
    source = (PROJECT_ROOT / relative_path).resolve()
    if not source.is_relative_to(PROJECT_ROOT) or not source.is_file():
        raise ValueError("Candidate source path is missing or outside this project.")
    return source


def approved_copy(source: Path, material_class: str) -> Path:
    destination_folder = REVIEW_ROOT / "train" / material_class
    destination_folder.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(source)

    for split in ("train", "valid", "test"):
        for class_name in CLASSES:
            for existing in (REVIEW_ROOT / split / class_name).glob("*"):
                if existing.is_file() and existing.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}:
                    if sha256(existing) == source_hash:
                        raise ValueError(f"Exact duplicate already staged at {existing.relative_to(PROJECT_ROOT)}.")

    destination = destination_folder / source.name
    if destination.exists():
        destination = destination_folder / f"{source.stem}_{source_hash[:8]}{source.suffix.lower()}"
    shutil.copy2(source, destination)
    if sha256(destination) != source_hash:
        destination.unlink(missing_ok=True)
        raise OSError("Copied image failed the post-copy hash check.")
    return destination


def save_decision(candidate: dict[str, str], decision: str, reason: str) -> None:
    source = checked_source_path(candidate["image_path"])
    status = "approved" if decision in CLASSES else "rejected" if decision == "reject" else "needs_review"
    if status == "approved":
        copied_path = approved_copy(source, decision)
        st.session_state.last_copy = copied_path.relative_to(PROJECT_ROOT).as_posix()

    manifest = read_csv(MANIFEST_PATH)
    record = {
        "image_path": candidate["image_path"],
        "material_class": decision,
        "source_dataset": candidate["source_dataset"],
        "review_status": status,
        "review_reason": reason.strip(),
    }
    manifest = [row for row in manifest if row.get("image_path") != candidate["image_path"]]
    manifest.append(record)
    write_manifest(manifest)


if not BATCH_PATH.exists():
    st.error("No review batch exists. Run `prepare_review_batch.py` first.")
    st.stop()

batch = read_csv(BATCH_PATH)
manifest = read_csv(MANIFEST_PATH)
reviewed_by_path = {row.get("image_path", ""): row for row in manifest}
pending = [row for row in batch if row.get("image_path") not in reviewed_by_path]

counts = Counter(row.get("material_class", "") for row in manifest if row.get("review_status") == "approved")
summary = st.columns(6)
for column, material_class in zip(summary, CLASSES):
    column.metric(f"Approved {material_class}", counts[material_class])
st.caption(f"Batch: {len(batch)} candidates | Reviewed: {len(manifest)} | Awaiting review: {len(pending)}")

if st.session_state.get("last_copy"):
    st.success(f"Verified copy staged at `{st.session_state.pop('last_copy')}`")

if not pending:
    st.success("Every candidate in this batch has a recorded decision. No new labels were inferred.")
    if manifest:
        st.json(manifest, expanded=False)
    st.stop()

position = min(int(st.session_state.get("review_position", 0)), len(pending) - 1)
candidate = pending[position]
try:
    source_path = checked_source_path(candidate["image_path"])
    with Image.open(source_path) as opened:
        opened.verify()
    with Image.open(source_path) as opened:
        preview = ImageOps.exif_transpose(opened).convert("RGB")
except Exception as error:
    st.error(f"Image could not be decoded; do not approve it. Error: {error}")
    preview = None

image_column, review_column = st.columns([1.45, 1])
with image_column:
    st.subheader(f"Candidate {position + 1} of {len(pending)}")
    if preview is not None:
        st.image(preview, width="stretch")
    else:
        st.info("Unreadable candidates may only be rejected or marked needs_review.")

with review_column:
    st.subheader("Decision")
    st.caption("Source and filename are hidden here to reduce folder/name-driven labeling. The manifest records the source after submission.")
    st.caption("Reason must describe visible evidence. For steel/metal, include independent material evidence such as a part/specimen record.")
    decision = st.selectbox("Material class or outcome", ("select one", *DECISIONS))
    with st.form("manual_review", clear_on_submit=True):
        reason = st.text_area("Review reason / visible evidence", height=120)
        visible_evidence = st.checkbox("I based the decision on the actual image, not its path, filename, or defect annotation.")
        quality_ok = st.checkbox("The image is readable, reasonably clear, and has no disqualifying overlay or severe crop.")
        material_verified = True
        if decision in {"steel", "metal"}:
            material_verified = st.checkbox("I have independent evidence for steel vs. non-steel metal; appearance alone is insufficient.")
        unsupported_verified = True
        if decision == "unknown":
            unsupported_verified = st.checkbox("The visible inspected material/object is genuinely outside all five supported classes.")
        submitted = st.form_submit_button("Save decision", type="primary")

    if submitted:
        if decision == "select one":
            st.error("Choose a class, reject, or needs_review.")
        elif not reason.strip():
            st.error("Enter a concise reason for the decision.")
        elif decision in CLASSES and not visible_evidence:
            st.error("A class approval requires confirming the visible image evidence.")
        elif decision in CLASSES and not quality_ok:
            st.error("Do not approve an unclear, corrupted, or unsuitable image. Choose reject or needs_review.")
        elif decision in CLASSES and preview is None:
            st.error("Unreadable images cannot be approved. Choose reject or needs_review.")
        elif decision in {"steel", "metal"} and not material_verified:
            st.error("Keep steel/metal ambiguity as needs_review unless material identity is independently verified.")
        elif decision == "unknown" and not unsupported_verified:
            st.error("Do not approve unknown without confirming it is outside all supported classes.")
        else:
            try:
                save_decision(candidate, decision, reason)
                st.session_state.review_position = position
                st.rerun()
            except Exception as error:
                st.error(f"Decision was not saved: {error}")

nav_left, nav_right, source_info = st.columns([1, 1, 4])
with nav_left:
    if st.button("Previous", disabled=position == 0):
        st.session_state.review_position = position - 1
        st.rerun()
with nav_right:
    if st.button("Next", disabled=position >= len(pending) - 1):
        st.session_state.review_position = position + 1
        st.rerun()
with source_info:
    with st.expander("Reveal source path (do this after deciding from the image)"):
        st.code(candidate["image_path"])
        st.caption(f"Candidate pool: {candidate['source_dataset']}")

with st.expander("Review manifest"):
    st.json(manifest, expanded=False)
