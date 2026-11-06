# Manual Material Review

This is a separate, review-only utility. It does not train or integrate a model, and it does not alter source datasets.

## Prepare a batch

From the project root, run:

```powershell
.\.venv\Scripts\python.exe material_classification_dataset\prepare_review_batch.py
```

The script chooses 12 candidates from each of the six source pools (72 total), with no labels assigned. It checks that sampled files decode and drops exact byte duplicates and same-name augmentation families from the batch. The sample is deterministic. A pending batch is never overwritten unless `--force` is provided; do not use `--force` after reviewing any item.

## First-pass visual screening

`candidate_visual_screening.csv` is a separate, unapproved screening queue for the images referenced by `ai_screening_manifest.csv`. It was generated with the already-cached OpenCLIP ViT-B/32 checkpoint in offline mode; it contains model-similarity screening signals, not verified human observations or material labels. Every row still requires human review. `ambiguous` means the signal was not sufficiently separated; `metal_appearance_unspecified` must never be converted to `steel` or non-steel `metal` without traceable material evidence. `reject_unusable` is a review flag, not an executed rejection. `evidence_reference` is blank unless independent evidence is actually supplied. This file does not modify `review_manifest.csv`, copy images, or prepare training data.

To repeat screening, run from the project root:

```powershell
.\.venv\Scripts\python.exe material_classification_dataset\screen_source_images.py
```

The script requires the existing local checkpoint and disables Hugging Face network access. It does not download weights or train a model.

## Prepare a traceable human-review dataset

From the project root, run:

```powershell
.\.venv\Scripts\python.exe material_classification_dataset\prepare_review_dataset.py
```

This validates and joins the source-image manifest, per-image YOLO annotation-file paths, collection documentation references, existing review decisions, and unverified OpenCLIP screening signals into `human_review_preparation.csv`. `HUMAN_REVIEW_PREPARATION_REPORT.md` records the audit counts and evidence limitations. Collection-level descriptions create review candidates only; they do not verify an individual image. `metal_unspecified` is deliberately not a non-steel `metal` label. No images are copied, and the existing review manifest is not modified.

## Resumable human-review workflow

```powershell
.\.venv\Scripts\python.exe -m streamlit run material_classification_dataset\human_review_app.py
```

The app shows one image at a time and saves resumable decisions to the separate `human_review_decisions.csv`. It does not change `review_manifest.csv`, copy images, or write labels into training folders. The eight explicit decisions are Steel, Metal, Fabric, PCB, Welding, Unknown, Unusable, and Needs Review. Every saved decision requires a reviewer rationale. Approved labels require an evidence-reference field; if none exists, enter `none`, which is reported as lacking evidence. Steel and Metal require an actual traceable reference that distinguishes steel from non-steel; appearance alone is not enough. Unknown requires explicit confirmation that the item is outside supported classes. Unusable requires explicit reviewer confirmation and is stored as rejected. A missing/unreadable image is not auto-rejected.

The app provides previous/next, skip, search and class/status filters. It updates a decision by stable `image_path` instead of creating a conflicting row. Preparation evidence and OpenCLIP signals are displayed as context only; YOLO defect labels are explicitly not material labels. The old `review_app.py` is a separate legacy batch tool that writes `review_manifest.csv` and copies approved files; do not use it for this resumable workflow.

## Duplicate audit, progress, and readiness

Run these from the project root:

```powershell
.\.venv\Scripts\python.exe material_classification_dataset\audit_human_review.py duplicates
.\.venv\Scripts\python.exe material_classification_dataset\audit_human_review.py progress
.\.venv\Scripts\python.exe material_classification_dataset\audit_human_review.py readiness
```

`duplicates` creates `DUPLICATE_REVIEW_REPORT.md` with duplicate paths, byte-identical SHA-256 groups, matching basenames, and possible Roboflow augmentation-family groups. It does not delete or alter any image; same-name/family groups are leads for human inspection, not proof of duplicate content. Read and resolve those groups before rerunning readiness with `--duplicates-reviewed`. Readiness intentionally has no default sample-size threshold: after choosing one for the intended use case, pass it with `--min-per-class N` (replace `N` with that positive integer). The checker also requires all six approved classes, valid paths, evidence references, explicit Unknown confirmation, documented Steel/Metal distinction, complete decision fields, and duplicate-handling attestation. It reports `NOT READY FOR TRAINING` until every check passes and never trains a model.

`progress` regenerates `HUMAN_REVIEW_PROGRESS.md` from the decision CSV. Decisions are actual human inputs only; the application and audit tools create no example or test labels.
