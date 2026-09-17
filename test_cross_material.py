import sys, cv2, numpy as np
sys.path.insert(0, r'd:\quality-inspection-system')
from backend.services.inference_service import run_inference

tests = [
    (r'd:\quality-inspection-system\vision\test_images\fabrics_test\image1.jpg', 'steel', 'fabric_img+steel_model'),
    (r'd:\quality-inspection-system\vision\test_images\metal_test\metal_test1.jpg', 'fabric', 'metal_img+fabric_model'),
    (r'd:\quality-inspection-system\vision\test_images\steel_test\image1.jpeg', 'metal', 'steel_img+metal_model'),
    (r'd:\quality-inspection-system\vision\test_images\pcb_test\missing_hole50_y0_x0_jpg.rf.6487d1e53d26f0d8bc7df9a4e87c659a.jpg', 'welding', 'pcb_img+welding_model'),
    (r'd:\quality-inspection-system\vision\test_images\welding_test\bad_weld_vid198_jpeg_jpg.rf.138e8a0d153bfd9f1a07f9e56302661a.jpg', 'pcb', 'weld_img+pcb_model'),
]

# Also test blank image
blank = np.zeros((640, 640, 3), dtype=np.uint8)
for mat in ['steel', 'metal', 'fabric', 'pcb', 'welding']:
    r = run_inference(blank, mat)
    print(f'BLANK+{mat}_model -> {r["status"]} defects:{r["total_defects"]}')

print()
for path, mat, label in tests:
    img = cv2.imread(path)
    if img is None:
        print(label, ': LOAD FAILED')
        continue
    r = run_inference(img, mat)
    dets = [(d['class_name'], d['confidence']) for d in r['detections']]
    print(label, '->', r['status'], 'defects:', r['total_defects'], 'dets:', dets[:3])
