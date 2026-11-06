import csv
import os
from collections import Counter
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import open_clip
import torch
from PIL import Image, UnidentifiedImageError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = Path(__file__).resolve().parent
INPUT_CSV = DATASET_DIR / "ai_screening_manifest.csv"
OUTPUT_CSV = DATASET_DIR / "candidate_visual_screening.csv"
CHECKPOINT = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--laion--CLIP-ViT-B-32-laion2B-s34B-b79K"
    / "snapshots"
    / "1a25a446712ba5ee05982a381eed697ef9b435cf"
    / "open_clip_model.safetensors"
)
BATCH_SIZE = 64
MIN_SCORE = 24.0
MIN_MARGIN = 3.0

PROMPTS = {
    "fabric": [
        "a close-up photo of textile fabric showing a woven or knitted fiber surface",
        "a photograph of cloth or fabric fibers",
    ],
    "pcb": [
        "a close-up photo of an electronic printed circuit board showing traces, pads or mounted components",
        "a photograph of a circuit board with electronic parts",
    ],
    "welding": [
        "a photograph of a weld bead or welded joint on a metal workpiece",
        "a photograph of an active welding arc with sparks",
    ],
    "unsupported_unknown": [
        "a photograph of an unknown material or object not identifiable as fabric, PCB or welding",
        "a photograph of a non-metal material surface",
    ],
    "metal_appearance_unspecified": [
        "a close-up photograph of a metal sheet surface with scratches or defects",
        "a photograph of a steel sheet surface with visible defects",
    ],
    "reject_unusable": [
        "a blank or unreadable image that is severely dark, blurred, or corrupted",
        "a completely black image with no discernible content",
    ],
}


def main() -> None:
    if not CHECKPOINT.is_file():
        raise FileNotFoundError(f"Cached CLIP checkpoint not found: {CHECKPOINT}")

    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as source:
        source_rows = list(csv.DictReader(source))

    paths = [(row, PROJECT_ROOT / row["image_path"]) for row in source_rows]
    missing = [row["image_path"] for row, path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} manifest source images are missing; no output written."
        )

    torch.set_num_threads(min(4, os.cpu_count() or 1))
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained=None, device="cpu"
    )
    open_clip.load_checkpoint(model, str(CHECKPOINT))
    model.eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    prompt_names = [
        (category, prompt)
        for category, prompts in PROMPTS.items()
        for prompt in prompts
    ]

    results = []
    errors = 0
    with torch.inference_mode():
        text = model.encode_text(tokenizer([prompt for _, prompt in prompt_names]))
        text /= text.norm(dim=-1, keepdim=True)

        for start in range(0, len(paths), BATCH_SIZE):
            batch = paths[start : start + BATCH_SIZE]
            valid_images = []
            valid_records = []

            for row, path in batch:
                try:
                    with Image.open(path) as image:
                        image.verify()
                    with Image.open(path) as image:
                        dimensions = f"{image.width}x{image.height}"
                        valid_images.append(preprocess(image.convert("RGB")))
                        valid_records.append((row, dimensions))
                except (OSError, UnidentifiedImageError, ValueError) as exc:
                    errors += 1
                    results.append(
                        {
                            "image_path": row["image_path"],
                            "proposed_material_class": "reject_unusable",
                            "source_dataset": row["source_dataset"],
                            "proposal_status": "needs_human_review_unreadable",
                            "visible_evidence_reason": (
                                "Image could not be decoded by the local image reader; "
                                f"inspect the original file. Error: {exc}"
                            ),
                            "evidence_reference": "",
                            "screening_signal": "image_decode_error",
                        }
                    )

            if not valid_images:
                continue

            pixels = torch.stack(valid_images)
            image_features = model.encode_image(pixels)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            similarities = (100.0 * image_features @ text.T).tolist()

            for (row, dimensions), scores in zip(valid_records, similarities):
                category_scores = {}
                offset = 0
                for category, prompts in PROMPTS.items():
                    category_scores[category] = sum(
                        scores[offset : offset + len(prompts)]
                    ) / len(prompts)
                    offset += len(prompts)

                ranked = sorted(
                    category_scores.items(), key=lambda item: item[1], reverse=True
                )
                top_category, top_score = ranked[0]
                margin = top_score - ranked[1][1]
                if top_score >= MIN_SCORE and margin >= MIN_MARGIN:
                    proposed_class = top_category
                    status = "screening_candidate_needs_human_review"
                    reason = (
                        "Local OpenCLIP visual-similarity screening signal only; "
                        f"top prompt group={top_category}, score={top_score:.2f}, "
                        f"margin={margin:.2f}, image_dimensions={dimensions}. "
                        "Not a verified visible-evidence finding or approved label. "
                        "Human review required."
                    )
                    if top_category == "metal_appearance_unspecified":
                        reason += " Metal appearance cannot establish steel versus non-steel."
                else:
                    proposed_class = "ambiguous"
                    status = "ambiguous_needs_human_review"
                    reason = (
                        "No sufficiently separated local OpenCLIP visual-similarity "
                        f"screening result (top={top_category}, score={top_score:.2f}, "
                        f"margin={margin:.2f}, image_dimensions={dimensions}); "
                        "human review required."
                    )

                results.append(
                    {
                        "image_path": row["image_path"],
                        "proposed_material_class": proposed_class,
                        "source_dataset": row["source_dataset"],
                        "proposal_status": status,
                        "visible_evidence_reason": reason,
                        "evidence_reference": "",
                        "screening_signal": (
                            f"OpenCLIP ViT-B/32 similarity; "
                            + "; ".join(
                                f"{category}={score:.2f}"
                                for category, score in ranked
                            )
                        ),
                    }
                )

            done = min(start + len(batch), len(paths))
            if done % 2048 < BATCH_SIZE or done == len(paths):
                print(f"Screened {done}/{len(paths)} source images", flush=True)

    fields = [
        "image_path",
        "proposed_material_class",
        "source_dataset",
        "proposal_status",
        "visible_evidence_reason",
        "evidence_reference",
        "screening_signal",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    class_counts = Counter(row["proposed_material_class"] for row in results)
    status_counts = Counter(row["proposal_status"] for row in results)
    print(f"Total screened: {len(results)}")
    print(f"Unreadable: {errors}")
    print(f"Class counts: {dict(class_counts)}")
    print(f"Status counts: {dict(status_counts)}")
    print(f"Proposal file: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
