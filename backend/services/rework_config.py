"""
Rework Rules & Cost Configuration
===================================
Single source of truth for:
  - Material-specific rework recommendations (keyed by defect class name)
  - Configurable cost parameters per material/defect

All values are configurable here — no logic is duplicated in the frontend.

Cost formula (per defect instance):
    estimated_cost = labor_cost + material_cost + processing_cost

Currency is configurable via COST_CURRENCY env var (default: USD).
If any cost component is None the estimate is marked unavailable.

Quality decision thresholds (configurable, used by report endpoint):
    0 defects  → PASS
    1 defect   → REWORK
    ≥2 defects → FAIL
These thresholds are already applied by the existing evaluators; this
config is used only for the report narrative — it does NOT override the
stored status.
"""
import os

COST_CURRENCY = os.environ.get("COST_CURRENCY", "USD")

# ── Quality decision thresholds (informational — stored status is authoritative) ──
QUALITY_THRESHOLDS = {
    "pass_max_defects":   0,   # 0 defects → PASS
    "rework_max_defects": 1,   # 1 defect  → REWORK
    # ≥2 defects → FAIL
}

# ── Rework rules ──────────────────────────────────────────────────────
# Structure per entry:
#   method        : recommended rework action
#   reason        : why this action is recommended
#   expected_outcome : what to expect after rework
#   reinspect     : bool — is re-inspection recommended?
#   labor_cost    : float or None (USD per defect instance)
#   material_cost : float or None
#   processing_cost: float or None

REWORK_RULES: dict[str, dict[str, dict]] = {
    "steel": {
        "Scratches": {
            "method": "Surface polishing / abrasive finishing",
            "reason": "Surface scratches reduce structural integrity and aesthetic quality of steel products.",
            "expected_outcome": "Removal or significant reduction of surface scratches. Re-inspection required to confirm surface meets specification.",
            "reinspect": True,
            "labor_cost": 12.00,
            "material_cost": 3.50,
            "processing_cost": 5.00,
        },
        "Dents": {
            "method": "Mechanical straightening / press forming",
            "reason": "Dents indicate deformation that may compromise dimensional tolerances.",
            "expected_outcome": "Restoration of surface geometry within tolerance. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 18.00,
            "material_cost": 2.00,
            "processing_cost": 8.00,
        },
        "Rust": {
            "method": "Chemical rust removal + protective coating application",
            "reason": "Rust indicates oxidation that will progress and compromise structural integrity if untreated.",
            "expected_outcome": "Removal of oxidation layer and application of corrosion-resistant coating. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 22.00,
            "material_cost": 15.00,
            "processing_cost": 10.00,
        },
        "Other": {
            "method": "Manual inspection and targeted surface treatment",
            "reason": "Unclassified defect requires manual assessment before rework method can be determined.",
            "expected_outcome": "Defect assessed and treated per manual inspection findings. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 15.00,
            "material_cost": 5.00,
            "processing_cost": 6.00,
        },
    },
    "metal": {
        "inclusion": {
            "method": "Grinding / machining to remove inclusion",
            "reason": "Inclusions are foreign material embedded in the metal that weaken the structure.",
            "expected_outcome": "Removal of inclusion and surface restoration. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 20.00,
            "material_cost": 4.00,
            "processing_cost": 9.00,
        },
        "oil_spot": {
            "method": "Solvent degreasing / ultrasonic cleaning",
            "reason": "Oil contamination prevents proper coating adhesion and indicates process contamination.",
            "expected_outcome": "Complete removal of oil contamination. Surface ready for coating. Re-inspection recommended.",
            "reinspect": True,
            "labor_cost": 8.00,
            "material_cost": 6.00,
            "processing_cost": 3.00,
        },
        "punching_hole": {
            "method": "Weld fill and re-machining or part replacement",
            "reason": "Unintended punching holes compromise structural integrity and cannot be surface-treated.",
            "expected_outcome": "Hole filled and surface restored, or part replaced. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 35.00,
            "material_cost": 20.00,
            "processing_cost": 15.00,
        },
        "silk_spot": {
            "method": "Surface buffing / polishing",
            "reason": "Silk spots are surface irregularities that affect finish quality.",
            "expected_outcome": "Surface finish restored to specification. Re-inspection recommended.",
            "reinspect": True,
            "labor_cost": 10.00,
            "material_cost": 2.50,
            "processing_cost": 4.00,
        },
        "water_spot": {
            "method": "Chemical cleaning and drying treatment",
            "reason": "Water spots indicate improper drying and may lead to corrosion if untreated.",
            "expected_outcome": "Spots removed and surface protected. Re-inspection recommended.",
            "reinspect": True,
            "labor_cost": 7.00,
            "material_cost": 3.00,
            "processing_cost": 2.50,
        },
        "welding_line": {
            "method": "Weld grinding and surface finishing",
            "reason": "Visible welding lines indicate incomplete finishing that does not meet surface specification.",
            "expected_outcome": "Weld line ground flush and surface finished to specification. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 16.00,
            "material_cost": 5.00,
            "processing_cost": 7.00,
        },
    },
    "fabric": {
        "color_bleeding": {
            "method": "Re-dyeing / color fixation treatment",
            "reason": "Color bleeding indicates dye instability that will worsen with washing or use.",
            "expected_outcome": "Color stabilized or fabric re-dyed to specification. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 14.00,
            "material_cost": 8.00,
            "processing_cost": 6.00,
        },
        "crease": {
            "method": "Steam pressing / heat treatment",
            "reason": "Creases affect product appearance and may indicate improper handling or storage.",
            "expected_outcome": "Creases removed and fabric restored to flat specification. Re-inspection recommended.",
            "reinspect": False,
            "labor_cost": 5.00,
            "material_cost": 0.50,
            "processing_cost": 2.00,
        },
        "hole": {
            "method": "Patch repair or fabric replacement",
            "reason": "Holes are structural defects that cannot be concealed and compromise product integrity.",
            "expected_outcome": "Hole patched (if within tolerance) or fabric section replaced. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 18.00,
            "material_cost": 12.00,
            "processing_cost": 5.00,
        },
    },
    "pcb": {
        "missing_hole": {
            "method": "Precision drilling at specified location",
            "reason": "Missing holes prevent component mounting and electrical connectivity.",
            "expected_outcome": "Hole drilled to specification. Electrical continuity test required. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 25.00,
            "material_cost": 2.00,
            "processing_cost": 12.00,
        },
        "mouse_bite": {
            "method": "Board edge trimming and re-profiling",
            "reason": "Mouse bite defects on board edges compromise mechanical fit and may cause shorts.",
            "expected_outcome": "Edge restored to specification. Dimensional check required. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 20.00,
            "material_cost": 3.00,
            "processing_cost": 10.00,
        },
        "open_circuit": {
            "method": "Trace repair using conductive ink or micro-soldering",
            "reason": "Open circuits cause complete functional failure of the affected circuit path.",
            "expected_outcome": "Circuit continuity restored. Full electrical test required. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 40.00,
            "material_cost": 15.00,
            "processing_cost": 20.00,
        },
        "short": {
            "method": "Solder bridge removal / trace isolation",
            "reason": "Short circuits cause functional failure and may damage components.",
            "expected_outcome": "Short removed and isolation confirmed. Full electrical test required. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 35.00,
            "material_cost": 5.00,
            "processing_cost": 18.00,
        },
        "spur": {
            "method": "Copper spur removal by micro-etching or mechanical trimming",
            "reason": "Copper spurs can cause intermittent shorts under vibration or thermal cycling.",
            "expected_outcome": "Spur removed and clearance verified. Re-inspection recommended.",
            "reinspect": True,
            "labor_cost": 22.00,
            "material_cost": 4.00,
            "processing_cost": 10.00,
        },
        "spurious_copper": {
            "method": "Chemical etching to remove excess copper",
            "reason": "Spurious copper deposits can cause shorts and violate design rule checks.",
            "expected_outcome": "Excess copper removed and clearances verified. Re-inspection required.",
            "reinspect": True,
            "labor_cost": 28.00,
            "material_cost": 8.00,
            "processing_cost": 14.00,
        },
    },
    "welding": {
        "bad_weld": {
            "method": "Weld removal (grinding) and re-welding to specification",
            "reason": "Bad welds indicate incomplete fusion, porosity, or incorrect parameters that compromise joint strength.",
            "expected_outcome": "Defective weld removed and replaced with compliant weld. NDT/visual re-inspection required.",
            "reinspect": True,
            "labor_cost": 45.00,
            "material_cost": 18.00,
            "processing_cost": 22.00,
        },
        "good_weld": {
            # good_weld is not a defect — no rework needed
            "method": "No rework required",
            "reason": "Detection classified as acceptable weld quality.",
            "expected_outcome": "No action required.",
            "reinspect": False,
            "labor_cost": 0.0,
            "material_cost": 0.0,
            "processing_cost": 0.0,
        },
    },
}


def get_rework_rule(material: str, defect_class: str) -> dict | None:
    """
    Return the rework rule for a given material + defect class.
    Returns None if no rule is configured.
    """
    mat_rules = REWORK_RULES.get(material.lower(), {})
    # Try exact match first, then case-insensitive
    rule = mat_rules.get(defect_class)
    if rule is None:
        for key, val in mat_rules.items():
            if key.lower() == defect_class.lower():
                rule = val
                break
    return rule


def compute_cost_estimate(material: str, defects: list[dict]) -> dict:
    """
    Compute total estimated rework cost from real defect list.

    Parameters
    ----------
    material : str
    defects  : list of dicts with at least 'defect_class' key

    Returns
    -------
    dict with keys:
        available       : bool
        total           : float | None
        currency        : str
        breakdown       : list of per-defect cost dicts
        note            : str
    """
    if not defects:
        return {
            "available": False,
            "total": None,
            "currency": COST_CURRENCY,
            "breakdown": [],
            "note": "No defects detected — no rework cost applicable.",
        }

    breakdown = []
    total = 0.0
    any_missing = False

    for d in defects:
        cls = d.get("defect_class") or d.get("class_name") or d.get("class", "unknown")
        rule = get_rework_rule(material, cls)
        if rule is None:
            any_missing = True
            breakdown.append({
                "defect_class": cls,
                "labor_cost": None,
                "material_cost": None,
                "processing_cost": None,
                "subtotal": None,
                "note": "No cost rule configured for this defect type.",
            })
            continue

        lc = rule.get("labor_cost")
        mc = rule.get("material_cost")
        pc = rule.get("processing_cost")

        if lc is None or mc is None or pc is None:
            any_missing = True
            breakdown.append({
                "defect_class": cls,
                "labor_cost": lc,
                "material_cost": mc,
                "processing_cost": pc,
                "subtotal": None,
                "note": "Partial cost data — configure missing parameters.",
            })
        else:
            sub = lc + mc + pc
            total += sub
            breakdown.append({
                "defect_class": cls,
                "labor_cost": lc,
                "material_cost": mc,
                "processing_cost": pc,
                "subtotal": round(sub, 2),
                "note": "ESTIMATED",
            })

    if any_missing:
        note = (
            "Cost estimate unavailable — configure material-specific rework "
            "cost parameters in backend/services/rework_config.py."
        )
        return {
            "available": False,
            "total": None,
            "currency": COST_CURRENCY,
            "breakdown": breakdown,
            "note": note,
        }

    return {
        "available": True,
        "total": round(total, 2),
        "currency": COST_CURRENCY,
        "breakdown": breakdown,
        "note": "ESTIMATED — actual costs may vary. All values are estimates only.",
    }
