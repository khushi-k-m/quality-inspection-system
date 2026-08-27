"""
MetalEvaluator
==============
Converts a list of YOLO detections (from MetalInspector) into a
structured quality-inspection result.

Scoring system
--------------
This is a project-level engineering scoring system designed to be easy
to tune later using real inspection data.  It is NOT scientifically
validated.

Defect penalty weights (points deducted per detected instance):
    inclusion      : 20  — structural integrity risk
    punching_hole  : 25  — severe structural defect
    welding_line   : 15  — process defect, may affect strength
    oil_spot       : 10  — surface contamination
    water_spot     : 8   — minor surface contamination
    silk_spot      : 5   — cosmetic defect

Status thresholds:
    score >= 80  → PASS    (LOW severity)
    score >= 55  → REWORK  (MEDIUM severity)
    score <  55  → FAIL    (HIGH severity)

If any structural defect (inclusion or punching_hole) is detected,
status is forced to FAIL regardless of score.
"""

# Penalty points deducted per detected instance of each defect class.
# Tune these values based on real inspection data.
DEFECT_PENALTIES = {
    "inclusion":     20,
    "punching_hole": 25,
    "welding_line":  15,
    "oil_spot":      10,
    "water_spot":     8,
    "silk_spot":      5,
}

# Defects that immediately force a FAIL regardless of total score.
CRITICAL_DEFECTS = {"inclusion", "punching_hole"}

# Status thresholds
PASS_THRESHOLD   = 80
REWORK_THRESHOLD = 55


class MetalEvaluator:
    """
    Evaluates metal surface quality from a list of YOLO detections.

    Parameters
    ----------
    detections : list of dict
        Output from MetalInspector.inspect().
    """

    def evaluate(self, detections: list) -> dict:
        """
        Parameters
        ----------
        detections : list of dict
            Each dict must contain at least 'class_name' and 'confidence'.

        Returns
        -------
        dict with keys:
            quality_score : int   (0 – 100)
            severity      : str   (LOW / MEDIUM / HIGH)
            status        : str   (PASS / REWORK / FAIL)
            defect_count  : int
            defects       : list  (same as input detections)
            remarks       : str
        """
        defect_count = len(detections)

        # ── No defects ────────────────────────────────────────────────
        if defect_count == 0:
            return {
                "quality_score": 100,
                "severity":      "LOW",
                "status":        "PASS",
                "defect_count":  0,
                "defects":       [],
                "remarks":       (
                    "No defects detected. "
                    "Metal surface meets quality requirements."
                ),
            }

        # ── Calculate score ───────────────────────────────────────────
        score = 100
        has_critical = False

        for det in detections:
            name    = det.get("class_name", "").lower()
            penalty = DEFECT_PENALTIES.get(name, 10)
            score  -= penalty
            if name in CRITICAL_DEFECTS:
                has_critical = True

        score = max(0, min(100, score))

        # ── Determine status / severity ───────────────────────────────
        if has_critical or score < REWORK_THRESHOLD:
            status   = "FAIL"
            severity = "HIGH"
        elif score < PASS_THRESHOLD:
            status   = "REWORK"
            severity = "MEDIUM"
        else:
            status   = "PASS"
            severity = "LOW"

        # ── Build remarks ─────────────────────────────────────────────
        class_counts = {}
        for det in detections:
            name = det.get("class_name", "unknown")
            class_counts[name] = class_counts.get(name, 0) + 1

        defect_summary = ", ".join(
            f"{count}x {name}" for name, count in class_counts.items()
        )

        if status == "FAIL":
            remarks = (
                f"Critical defects detected: {defect_summary}. "
                "Metal surface does not meet quality requirements. "
                "Immediate corrective action required."
            )
        elif status == "REWORK":
            remarks = (
                f"Defects detected: {defect_summary}. "
                "Metal surface requires rework or manual inspection."
            )
        else:
            remarks = (
                f"Minor defects detected: {defect_summary}. "
                "Metal surface meets quality requirements with minor issues."
            )

        return {
            "quality_score": score,
            "severity":      severity,
            "status":        status,
            "defect_count":  defect_count,
            "defects":       detections,
            "remarks":       remarks,
        }
