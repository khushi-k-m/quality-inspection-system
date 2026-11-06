# Material Classification Candidate Collection Report

**Status:** Candidate discovery only. No images were moved or copied during this review, and no model was trained.

## Scope and method

The six defect-dataset roots contain 29,187 images total. I reviewed evenly spaced visual samples of 48 images from each root (288 images total), reviewed all 154 images in the project's `output/` capture/test/prediction folders as contact sheets, and checked the dataset provenance notes. This is a source-screening review, not a per-image audit; group counts below are source-pool counts, not verified class counts. Do not bulk-label or import a group based on this report alone.

## Candidate sources

| Proposed class | Candidate source group | Image count | Evidence and confidence | Manual verification |
|---|---|---:|---|---|
| steel | [`dataset`](../dataset/) | 6,666 | The source README identifies the upstream collection as Severstal steel-defect detection; reviewed samples show metal-sheet surfaces. **Medium-high source confidence; individual item confirmation remains necessary.** | Yes. Check every selected image against source/material provenance and exclude ambiguous or mixed-material views. |
| metal | [`dataset_metal`](../dataset_metal/) | 5,472 | The source documentation describes metal-surface defect imagery, and samples visibly show metal-like sheet surfaces. **High confidence that images depict metal; low confidence that they are non-steel.** | Yes. Do not assign to the project's generic `metal` class until steel vs non-steel is resolved. The README says there are three generated variants per source image, so deduplicate by original source before selecting or splitting. |
| metal | [`output/metal_capture`](../output/metal_capture/) | 54 | Captured inspection images show sheet/metal-like parts. Some entries visibly contain detection boxes or repeated views. **Medium confidence for metal appearance; low for non-steel.** | Yes. Locate clean originals and establish material; reject annotated composites as classifier inputs. |
| fabric | [`dataset_fabric`](../dataset_fabric/) | 5,104 | Upstream documentation identifies a fabric-defect collection; reviewed samples are consistent with fabric-like surface imagery. **Medium confidence.** | Yes. Confirm textile structure is visible and exclude smooth/ambiguous images. |
| fabric | [`output/fabric_capture`](../output/fabric_capture/) | 4 | One image ([FINSP20260831230501119547_PASS.jpg](../output/fabric_capture/FINSP20260831230501119547_PASS.jpg)) visibly shows cloth folds/weave. The other three look like smooth panels or have overlays, with no clear textile evidence. **High for that one image only; low for the other three.** | Review the one visible textile image; leave the other three unassigned unless their originals establish fabric. |
| pcb | [`dataset_pcb_boards`](../dataset_pcb_boards/) | 3,079 | The reviewed samples visibly show PCB traces, pads, and board substrate. **High visual confidence for the reviewed sample; source-wide verification is still needed.** | Yes. Prefer full, clean board images; verify selected files and group by physical board before splitting. |
| pcb | [`output/pcb_capture`](../output/pcb_capture/), [`output/pcb_test`](../output/pcb_test/) | 5 + 13 | The images visibly show circuit boards, but several contain model annotations/crops. **High for PCB identity; mixed suitability.** | Yes. Use only clean original images without prediction overlays. |
| welding | [`dataset_welding`](../dataset_welding/) | 5,093 | Reviewed samples show weld beads/joints. Some examples are screenshots, watermarked, or have other materials/backgrounds. **Medium-high for visible welding; mixed image quality.** | Yes. Verify each image visibly centers a weld and does not rely on annotation text or filename. |
| welding | [`output/welding_capture`](../output/welding_capture/), [`output/welding_test`](../output/welding_test/) | 5 + 20 | Captures show real weld joints; the test folder includes detection overlays and repeated/annotated views. **High for welding in clean captures; lower for annotated test images.** | Yes. Keep only clean originals and avoid duplicate frames/views. |
| unknown | [`dataset_wood_surface`](../dataset_wood_surface/) | 3,773 | Its README documents real European beech-board imagery; the reviewed images visibly show wood. Wood is outside the five supported categories. **High confidence as a source for a wood subset of `unknown`.** | Yes. Confirm each chosen frame clearly shows wood as the inspected material and remove samples dominated by text, labels, or unrelated objects. This single source is not sufficient coverage for `unknown`. |

The candidate counts are not additive across supplementary `output/` sources to the 29,187 dataset-root total. Output images may repeat source scenes or one another; no exact/near-duplicate scan was performed.

## Ambiguous or rejected as-is

- **Steel vs. metal:** The close-up metal surfaces in `dataset` and `dataset_metal` are visually alike. Source provenance makes `dataset` a steel-review candidate, but visual appearance alone cannot prove steel. `dataset_metal` cannot safely populate a separate *non-steel* class without material records.
- **Label ontology:** `steel` is a material, `metal` may include steel, and `welding` describes a process/joint rather than a mutually exclusive material. Define mutually exclusive class rules before labeling; otherwise the same welded-steel image could validly fit multiple classes.
- **Fabric capture:** Three of four images in `output/fabric_capture` are not visibly textile in the reviewed frames. Do not accept them merely because they are in that folder.
- **Wood metadata:** The wood README reports 2,641 train / 566 validation / 566 test images, but the current folders contain 2,641 / 755 / 377. Verify the split manifest and source grouping before using these for evaluation.
- **Prediction/result images:** `output/predictions` (8 images), `output/camera_capture` (33), and annotated/composite items in the material-specific output folders contain overlays, UI text, crops, or repeated views. Reject these files as classifier inputs unless clean originals are recovered.
- **Near duplicates/leakage:** Not assessed for the full corpus. The metal source's documented three variants per source image make split leakage a particular risk; keep all variants of one original together.

## Safe manual-review queue

The following groups are reasonable to inspect manually, not to auto-label: all six main source pools listed above, the 54 `output/metal_capture` images (after distinguishing non-steel from steel), the clean originals behind the PCB/welding output images, and the single clearly textile image in `output/fabric_capture`. For wood, review individual images from the documented beech-board pool as `unknown`; do not import the entire pool without checking visible content and duplicates.

No new candidates were copied. The three candidates staged during the prior dataset-preparation step remain as they were; this report does not change them or any source dataset.

## Real images still needed

- **Steel:** Clean, varied images with material identity traceable to a steel part/sample; include distinct product forms, finishes, scales, and lighting.
- **Metal:** If this means non-steel metal, collect traceable aluminum, copper, brass, or other explicitly defined non-steel samples. Do not use generic metal-looking surfaces as proof.
- **Fabric:** Additional clean textile images across weave/knit, fibers, colors, patterns, and folds, with different physical samples and capture sessions.
- **PCB:** Clean, varied board-level views from different physical boards and capture sessions, not only defect-centered crops.
- **Welding:** Clean weld-joint/bead images across varied joints and substrates, after defining whether this class takes precedence over the substrate material.
- **Unknown:** Diverse genuine unsupported materials/objects (for example plastic, glass, wood, ceramic, paper, or rubber), clearly outside all supported classes. Do not build this class from only wood or from images with empty defect labels.

Keep original/source IDs and material evidence with each selected image. Deduplicate by physical item and source image, then assign train/validation/test by item or capture session to avoid leakage. Do not train until labels, class boundaries, and split integrity have been manually confirmed.
