#!/usr/bin/env python
"""Test STEP 1: Material Registry"""
import os
from backend.services.material_registry import MATERIALS, get_material_config

print('=' * 60)
print('MATERIAL REGISTRY TEST - STEP 1')
print('=' * 60)

# Test 1: List all materials
print('\nRegistered materials:')
for material in sorted(MATERIALS.keys()):
    print(f'  ✓ {material}')

# Test 2: Verify all materials have required config
print('\nVerifying configuration for each material:')
for material in sorted(MATERIALS.keys()):
    try:
        cfg = get_material_config(material)
        print(f'\n  {material.upper()}:')
        print(f'    model_path: {cfg["model_path"]}')
        print(f'    db_path: {cfg["db_path"]}')
        print(f'    class_names: {cfg["class_names"]}')
        
        # Check if model file exists
        if os.path.exists(cfg['model_path']):
            print(f'    ✓ Model file exists')
        else:
            print(f'    ✗ Model file NOT FOUND')
    except Exception as e:
        print(f'  ERROR for {material}: {e}')

print('\n' + '=' * 60)
print('STEP 1 VERIFICATION COMPLETE')
print('=' * 60)
