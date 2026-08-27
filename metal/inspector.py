"""
MetalInspector
==============
Loads the trained Metal Surface YOLO model and runs object detection
on a given image path.  Returns structured detection results for every
defect found.

Defect classes (from dataset_metal/data.yaml):
    0 - inclusion
    1 - oil_spot
    2 - punching_hole
    3 - silk_spot
    4 - water_spot
    5 - welding_line
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    ROOT_DIR
    / "trained_model"
    / "metal_surface_model"
    / "weights"
    / "best.pt"
)

DEFAULT_CONFIDENCE = 0.25


class MetalInspector:
    """
    Wraps the Metal Surface YOLO model.

    Parameters
    ----------
    confidence : float
        Detection confidence threshold (0.0 – 1.0).
        Default is 0.25.
    """

    def __init__(self, confidence: float = DEFAULT_CONFIDENCE):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Metal model not found at:\n  {MODEL_PATH}\n"
                "Ensure the model has been trained and placed at the correct path."
            )

        self.confidence = confidence
        self._model = None  # lazy-load on first use

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_model(self):
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(str(MODEL_PATH))
        return self._model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inspect(self, image_path: str) -> list:
        """
        Run YOLO detection on *image_path*.

        Parameters
        ----------
        image_path : str or Path
            Absolute or relative path to the image file.

        Returns
        -------
        list of dict
            Each dict contains:
                class_id    : int
                class_name  : str
                confidence  : float  (0.0 – 1.0)
                x1, y1      : int    top-left corner
                x2, y2      : int    bottom-right corner
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        model = self._load_model()

        results = model.predict(
            source=str(image_path),
            conf=self.confidence,
            verbose=False,
            save=False,
        )

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                coords = box.xyxy[0].tolist()   # [x1, y1, x2, y2]

                detections.append({
                    "class_id":   cls_id,
                    "class_name": model.names.get(cls_id, f"class_{cls_id}"),
                    "confidence": round(conf, 4),
                    "x1": int(coords[0]),
                    "y1": int(coords[1]),
                    "x2": int(coords[2]),
                    "y2": int(coords[3]),
                })

        return detections

    def inspect_with_annotated(self, image_path: str) -> tuple:
        """
        Run detection and also return the annotated frame as JPEG bytes.

        Returns
        -------
        (detections: list, annotated_jpg: bytes)
        """
        import cv2
        import numpy as np

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        model = self._load_model()

        results = model.predict(
            source=str(image_path),
            conf=self.confidence,
            verbose=False,
            save=False,
        )

        detections = []

        for result in results:
            annotated = result.plot()

            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf   = float(box.conf[0])
                    coords = box.xyxy[0].tolist()

                    detections.append({
                        "class_id":   cls_id,
                        "class_name": model.names.get(cls_id, f"class_{cls_id}"),
                        "confidence": round(conf, 4),
                        "x1": int(coords[0]),
                        "y1": int(coords[1]),
                        "x2": int(coords[2]),
                        "y2": int(coords[3]),
                    })

        _, jpg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return detections, jpg.tobytes()
