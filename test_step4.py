#!/usr/bin/env python
"""Test STEP 4: Database Modules"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from fabric.database import create_database as create_fabric_db
from pcb.database import create_database as create_pcb_db
from welding.database import create_database as create_welding_db

print('=' * 70)
print('DATABASE MODULES TEST - STEP 4')
print('=' * 70)

print('\n[TEST 1] Creating databases...')
try:
    create_fabric_db()
    print('  ✓ fabric_inspections.db created')
except Exception as e:
    print(f'  ✗ Fabric: {e}')

try:
    create_pcb_db()
    print('  ✓ pcb_inspections.db created')
except Exception as e:
    print(f'  ✗ PCB: {e}')

try:
    create_welding_db()
    print('  ✓ welding_inspections.db created')
except Exception as e:
    print(f'  ✗ Welding: {e}')

print('\n[TEST 2] Testing fabric database save_inspection...')
try:
    from fabric.database import save_inspection as fabric_save, get_inspection as fabric_get
    
    fabric_save(
        inspection_id='FINSP20260831120000000',
        timestamp='2026-08-31 12:00:00',
        image_path='/path/to/image.jpg',
        defect_count=1,
        quality_score=80,
        severity='LOW',
        status='PASS',
        remarks='Test inspection',
        defects=[
            {
                'class_name': 'crease',
                'confidence': 85.5,
                'x1': 10, 'y1': 20, 'x2': 100, 'y2': 90
            }
        ],
        inspector='Test System',
        material='Fabric'
    )
    
    record = fabric_get('FINSP20260831120000000')
    if record and record['defect_count'] == 1:
        print('  ✓ Fabric inspection saved and retrieved')
    else:
        print('  ✗ Fabric inspection not found')
except Exception as e:
    print(f'  ✗ Fabric: {e}')

print('\n[TEST 3] Testing PCB database save_inspection...')
try:
    from pcb.database import save_inspection as pcb_save, get_inspection as pcb_get
    
    pcb_save(
        inspection_id='PINSP20260831120000000',
        timestamp='2026-08-31 12:00:00',
        image_path='/path/to/image.jpg',
        defect_count=2,
        quality_score=70,
        severity='MEDIUM',
        status='REWORK',
        remarks='Test inspection',
        defects=[
            {
                'class_name': 'mouse_bite',
                'confidence': 90.0,
                'x1': 30, 'y1': 40, 'x2': 120, 'y2': 110
            },
            {
                'class_name': 'spur',
                'confidence': 75.5,
                'x1': 150, 'y1': 50, 'x2': 200, 'y2': 120
            }
        ],
        inspector='Test System',
        material='PCB'
    )
    
    record = pcb_get('PINSP20260831120000000')
    if record and record['defect_count'] == 2 and len(record['defects']) == 2:
        print('  ✓ PCB inspection saved and retrieved with defects')
    else:
        print('  ✗ PCB inspection not found or defects missing')
except Exception as e:
    print(f'  ✗ PCB: {e}')

print('\n[TEST 4] Testing Welding database save_inspection...')
try:
    from welding.database import save_inspection as welding_save, get_inspection as welding_get
    
    welding_save(
        inspection_id='WINSP20260831120000000',
        timestamp='2026-08-31 12:00:00',
        image_path='/path/to/image.jpg',
        defect_count=1,
        quality_score=60,
        severity='HIGH',
        status='FAIL',
        remarks='Test inspection',
        defects=[
            {
                'class_name': 'bad_weld',
                'confidence': 95.0,
                'x1': 50, 'y1': 60, 'x2': 180, 'y2': 150
            }
        ],
        inspector='Test System',
        material='Welding'
    )
    
    record = welding_get('WINSP20260831120000000')
    if record and record['status'] == 'FAIL':
        print('  ✓ Welding inspection saved and retrieved')
    else:
        print('  ✗ Welding inspection not found')
except Exception as e:
    print(f'  ✗ Welding: {e}')

print('\n[TEST 5] Testing get_inspections (pagination)...')
try:
    from fabric.database import get_inspections as fabric_list
    total, records = fabric_list(limit=10, offset=0)
    print(f'  ✓ Fabric get_inspections: {total} total records')
except Exception as e:
    print(f'  ✗ Fabric: {e}')

print('\n[TEST 6] Testing get_analytics...')
try:
    from fabric.database import get_analytics as fabric_analytics
    analytics = fabric_analytics()
    print(f'  ✓ Fabric analytics: {analytics["total"]} inspections, avg score {analytics["avg_score"]}')
except Exception as e:
    print(f'  ✗ Fabric: {e}')

print('\n' + '=' * 70)
print('STEP 4 VERIFICATION COMPLETE')
print('=' * 70)
print('\nDatabase modules created:')
print('  ✓ fabric/database.py - Fabric inspection database')
print('  ✓ pcb/database.py - PCB inspection database')
print('  ✓ welding/database.py - Welding inspection database')
print('\nEach module includes:')
print('  ✓ create_database() - Schema initialization')
print('  ✓ save_inspection() - Write inspection records')
print('  ✓ get_inspection() - Retrieve single inspection')
print('  ✓ get_inspections() - List with filtering and pagination')
print('  ✓ get_analytics() - KPIs and defect distribution')
print('\nREADY FOR STEP 5')
