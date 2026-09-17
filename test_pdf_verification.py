"""
Comprehensive test: verify enhanced_report.py generates correct Page 2 for all 5 materials.
Tests data flow, not PDF text extraction (ReportLab uses ASCII85 encoding).
"""
import sys, os
sys.path.insert(0, r'd:\quality-inspection-system')

from backend.api.report_detail import (
    _get_record, _build_defect_stats, _build_heatmap,
    _build_recommendations, _get_historical,
)
from backend.services.rework_config import compute_cost_estimate, QUALITY_THRESHOLDS

TESTS = [
    ('INSP20260902145643765785', 'steel'),
    ('MINSP20260828145354371356', 'metal'),
    ('FINSP20260902215853562416', 'fabric'),
    ('PINSP20260902220215174704', 'pcb'),
    ('WINSP20260902214700607510', 'welding'),
]

PASS = 0
FAIL = 0

def check(label, condition, detail=''):
    global PASS, FAIL
    if condition:
        print(f'  PASS  {label}')
        PASS += 1
    else:
        print(f'  FAIL  {label}  {detail}')
        FAIL += 1

for iid, mat in TESTS:
    print(f'\n{"="*60}')
    print(f'MATERIAL: {mat.upper()}  |  ID: {iid}')
    print('='*60)

    # 1. Record fetch
    record = _get_record(iid, mat)
    check('Record fetched', record is not None)
    if record is None:
        print('  SKIP (no record)')
        continue

    check('Has status',        bool(record.get('status')))
    check('Has quality_score', record.get('quality_score') is not None)
    check('Has material',      bool(record.get('material')))

    defects    = record.get('defects', [])
    image_path = record.get('image_path')

    # 2. Defect stats
    stats = _build_defect_stats(defects, image_path)
    enriched = stats.pop('enriched_defects')
    check('Stats built',       isinstance(stats, dict))
    check('Total defects key', 'total_defects' in stats)
    check('by_type key',       'by_type' in stats)
    check('area_pct_available key', 'area_pct_available' in stats)

    area_avail = stats.get('area_pct_available', False)
    if mat == 'steel':
        check('Steel: area_pct NOT available (no bbox)', not area_avail)
    else:
        print(f'  INFO  {mat} area_pct_available={area_avail}')

    # 3. Heatmap
    heatmap = _build_heatmap(enriched, image_path)
    check('Heatmap built',     isinstance(heatmap, dict))
    check('Heatmap has available key', 'available' in heatmap)
    if mat == 'steel':
        check('Steel: heatmap unavailable (no bbox)', not heatmap.get('available'))
    else:
        print(f'  INFO  {mat} heatmap available={heatmap.get("available")}')
        if heatmap.get('available'):
            check('Heatmap grid is list', isinstance(heatmap.get('grid'), list))

    # 4. Recommendations
    rec = _build_recommendations(mat, enriched)
    check('Recommendations built', isinstance(rec, dict))
    check('Rec has applicable key', 'applicable' in rec)
    check('Rec has items key',      'items' in rec)
    if rec.get('applicable') and rec.get('items'):
        item = rec['items'][0]
        check('Rec item has method',           bool(item.get('method')))
        check('Rec item has reason',           bool(item.get('reason')))
        check('Rec item has expected_outcome', bool(item.get('expected_outcome')))
        check('Rec item has reinspect',        'reinspect' in item)

    # 5. Cost estimate
    cost = compute_cost_estimate(mat, enriched)
    check('Cost estimate built',    isinstance(cost, dict))
    check('Cost has available key', 'available' in cost)
    check('Cost has currency key',  'currency' in cost)
    check('Cost has breakdown key', 'breakdown' in cost)
    check('Cost has note key',      'note' in cost)

    # 6. Historical
    hist = _get_historical(mat)
    check('Historical built',              isinstance(hist, dict))
    check('Historical has total_inspections', 'total_inspections' in hist)
    check('Historical has status_distribution', 'status_distribution' in hist)
    total_insp = hist.get('total_inspections', 0)
    print(f'  INFO  {mat} total_inspections={total_insp}')

    # 7. Quality thresholds
    check('QUALITY_THRESHOLDS has pass_max_defects',   'pass_max_defects' in QUALITY_THRESHOLDS)
    check('QUALITY_THRESHOLDS has rework_max_defects', 'rework_max_defects' in QUALITY_THRESHOLDS)

    # 8. PDF generation
    from reports.enhanced_report import generate_enhanced_report
    pdf = generate_enhanced_report(iid, mat)
    check('PDF generated',    pdf is not None)
    if pdf:
        size = os.path.getsize(pdf)
        check('PDF non-empty', size > 10000, f'size={size}')
        print(f'  INFO  PDF: {pdf.name} ({size} bytes)')

print(f'\n{"="*60}')
print(f'RESULTS: {PASS} passed, {FAIL} failed')
print('='*60)
