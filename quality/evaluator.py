# ======================================================
# QUALITY EVALUATOR
# ======================================================

def evaluate_quality(
    scratches,
    dents,
    rust,
    other
):
    """
    Evaluate steel quality based on detected defects.

    Returns:
        quality_score
        status
        severity
        remarks
    """

    # ==================================================
    # TOTAL DEFECTS
    # ==================================================

    total_defects = (
        scratches +
        dents +
        rust +
        other
    )

    # ==================================================
    # QUALITY SCORE
    # ==================================================

    # Start with perfect quality.
    quality_score = 100

    # Defect penalties
    quality_score -= scratches * 10
    quality_score -= dents * 15
    quality_score -= rust * 30
    quality_score -= other * 10

    # Keep score between 0 and 100
    quality_score = max(
        0,
        min(100, quality_score)
    )

    # ==================================================
    # QUALITY STATUS
    # ==================================================

    # No defects
    if total_defects == 0:

        status = "PASS"
        severity = "NONE"

        remarks = (
            "No defects detected. "
            "Steel product meets quality requirements."
        )

    # Rust is considered a critical defect
    elif rust > 0:

        status = "FAIL"
        severity = "CRITICAL"

        remarks = (
            "Rust detected. "
            "Product requires immediate inspection "
            "and corrective action."
        )

    # Large number of defects
    elif total_defects > 2:

        status = "FAIL"
        severity = "HIGH"

        remarks = (
            "Multiple defects detected. "
            "Product does not meet quality requirements."
        )

    # Small number of defects
    else:

        status = "REWORK"
        severity = "MEDIUM"

        remarks = (
            "Minor defects detected. "
            "Product should undergo rework or manual inspection."
        )

    return {
        "quality_score": quality_score,
        "status": status,
        "severity": severity,
        "remarks": remarks,
        "total_defects": total_defects
    }


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    result = evaluate_quality(
        scratches=2,
        dents=1,
        rust=0,
        other=0
    )

    print("=" * 50)
    print("QUALITY EVALUATION TEST")
    print("=" * 50)

    print(
        f"Quality Score : {result['quality_score']}%"
    )

    print(
        f"Status        : {result['status']}"
    )

    print(
        f"Severity      : {result['severity']}"
    )

    print(
        f"Defects       : {result['total_defects']}"
    )

    print(
        f"Remarks       : {result['remarks']}"
    )

    print("=" * 50)