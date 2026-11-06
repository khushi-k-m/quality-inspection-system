# Human-review preparation audit

This is a review-preparation artifact only. It is not a labeled training dataset. No images were copied, moved, edited, rejected, or approved; no model was trained. Existing review decisions are carried through unchanged.

## Scope and evidence standard

- Unique source images in the output: **29,187**.
- Local source documentation and source URLs establish collection-level candidate context only. Folder names, filenames, YOLO defect classes, empty/nonempty annotations, dataset provenance, and OpenCLIP results do not establish an image-level material label.
- YOLO annotation paths are recorded for traceability. Their defect annotations provide no independent material confirmation by themselves.
- OpenCLIP values and flags are copied only as unverified screening signals; they do not decide class, usability, or approval.
- `metal_unspecified` means metal-versus-steel identity remains unresolved. It is not an assigned non-steel `metal` label.
- `unknown_wood` is a collection-level candidate for review as an unsupported material, not a verified `unknown` label.
- Every image remains subject to human review. Queue labels are flags, not disposition decisions; possible-unusable rows were not rejected.

## Verified labels

| Material class | Verified images |
|---|---:|
| steel | 0 |
| metal | 0 |
| fabric | 0 |
| pcb | 0 |
| welding | 0 |
| unknown | 0 |

## Source-supported candidate counts (not verified labels)

| Candidate | Images | Evidence reliability |
|---|---:|---|
| steel | 6,666 | medium_collection_level_candidate_only |
| metal_unspecified | 5,472 | low_collection_level_candidate_only |
| fabric | 5,104 | medium_collection_level_candidate_only |
| pcb | 3,079 | high_collection_level_candidate_only |
| welding | 5,093 | high_collection_level_candidate_only |
| unknown_wood | 3,773 | high_collection_level_candidate_only |
| unresolved | 0 | none |

## Review queues and screening flags

The primary `review_queue` is exclusive (existing review decision takes priority, then possible-unusable flag, then ambiguous flag). Source-candidate classes and OpenCLIP flags are separately recorded per image and can overlap this queue.

| Queue | Images |
|---|---:|
| existing_needs_review_decision | 4 |
| possible_unusable_review_flag | 1,525 |
| ambiguous_screening_flag | 22,370 |
| source_candidate_review | 5,288 |

| OpenCLIP screening signal (unverified) | Images |
|---|---:|
| ambiguous | 22,373 |
| metal_appearance_unspecified | 2,097 |
| pcb | 879 |
| reject_unusable | 1,525 |
| unsupported_unknown | 454 |
| welding | 1,859 |

## Evidence-reference counts

- Rows with a traceable collection-level local-document/source-URL reference: **29,187**.
- Rows with independent, image-specific material-evidence references: **0**.
- Existing review-manifest needs-review rows preserved: **4**; their evidence references remain blank.

## Source-pool audit

| Source manifest pool | Images | Collection-level candidate | Annotation files |
|---|---:|---|---:|
| dataset | 6,666 | steel | 6,666 |
| dataset_metal | 5,472 | metal_unspecified | 5,472 |
| dataset_fabric | 5,104 | fabric | 5,104 |
| dataset_pcb_boards | 3,079 | pcb | 3,079 |
| dataset_welding | 5,093 | welding | 5,093 |
| dataset_wood_surface | 3,773 | unknown_wood | 3,773 |

Annotation-file status totals: present_empty=2,474; present_nonempty=26,713.

## Training readiness

There are **0 verified image-level examples in every requested class**. There is not enough verified data to train a six-class classifier. First, humans must review each retained source image without relying on its directory name, filename, defect class, or OpenCLIP result; record an image-specific evidence source/reference and rationale for every proposed label. Steel and non-steel metal require traceable part/specimen/material documentation that resolves the distinction. Confirm fabric, PCB, and welding from the visible item or trustworthy item-specific records. Confirm `unknown` images are outside all five supported classes. Review possible-unusable images individually before excluding any. Resolve whether welding is a material class or an overlapping process label, then deduplicate physical items/capture sessions and build leakage-safe splits only after labels are verified.

Preparation manifest: `human_review_preparation.csv`.
