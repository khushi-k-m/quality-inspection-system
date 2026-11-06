import tempfile
import unittest
from pathlib import Path

from human_review_data import (
    DecisionValidationError,
    load_decisions,
    make_decision,
    save_decision,
    summarize_decisions,
)


class HumanReviewDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = {
            "image_path": "dataset_pcb_boards/valid/images/"
            "missing_hole01_y540_x1620_jpg.rf."
            "fbba73d796133b13500bdea19b465bf5.jpg",
            "source_dataset": "dataset_pcb_boards",
            "source_annotation_path": "dataset_pcb_boards/valid/labels/"
            "missing_hole01_y540_x1620_jpg.rf."
            "fbba73d796133b13500bdea19b465bf5.txt",
            "proposed_material_candidate": "pcb",
            "openclip_screening_signal_unverified": "unverified test signal",
        }

    def test_decision_records_traceable_metadata(self) -> None:
        record = make_decision(
            self.candidate,
            "PCB",
            "inspection-record-123",
            "Visible PCB substrate, traces, and component pads.",
            reviewer="reviewer",
        )
        self.assertEqual(record["review_status"], "approved")
        self.assertEqual(record["image_path"], self.candidate["image_path"])
        self.assertEqual(record["source_annotation_path"], self.candidate["source_annotation_path"])
        self.assertEqual(record["openclip_signal"], "unverified test signal")

    def test_steel_and_metal_require_traceable_evidence(self) -> None:
        for material in ("Steel", "Metal"):
            with self.subTest(material=material):
                with self.assertRaises(DecisionValidationError):
                    make_decision(
                        self.candidate,
                        material,
                        "none",
                        "Metal appearance alone is not sufficient.",
                    )

    def test_unknown_requires_explicit_confirmation(self) -> None:
        with self.assertRaises(DecisionValidationError):
            make_decision(
                self.candidate,
                "Unknown",
                "none",
                "Outside the supported materials.",
            )

    def test_unusable_requires_explicit_confirmation(self) -> None:
        with self.assertRaises(DecisionValidationError):
            make_decision(
                self.candidate,
                "Unusable",
                "none",
                "Image is unreadable.",
            )
        record = make_decision(
            self.candidate,
            "Unusable",
            "none",
            "Image is unreadable.",
            unusable_confirmed=True,
        )
        self.assertEqual(record["review_status"], "rejected")

    def test_save_resumes_and_updates_same_image_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "decisions.csv"
            save_decision(
                self.candidate,
                "PCB",
                "inspection-record-123",
                "Visible PCB substrate and copper traces.",
                path=path,
            )
            save_decision(
                self.candidate,
                "Needs Review",
                "none",
                "Original source evidence needs confirmation.",
                path=path,
            )
            rows = load_decisions(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["verified_material"], "Needs Review")
        self.assertEqual(rows[0]["review_status"], "needs_review")
        self.assertEqual(rows[0]["evidence_reference"], "none")

    def test_summary_counts_pending_and_unresolved_cases(self) -> None:
        preparation = [self.candidate, {**self.candidate, "image_path": "other.jpg"}]
        decision = make_decision(
            self.candidate,
            "Needs Review",
            "none",
            "Cannot resolve steel versus metal.",
            steel_metal_unresolved=True,
        )
        summary = summarize_decisions(preparation, [decision])
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["reviewed"], 1)
        self.assertEqual(summary["not_reviewed"], 1)
        self.assertEqual(summary["steel_metal_unresolved_count"], 1)


if __name__ == "__main__":
    unittest.main()
