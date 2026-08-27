import urllib.request
import urllib.parse
import json
import os

BASE = "http://127.0.0.1:8000"
ROOT = os.path.dirname(os.path.abspath(__file__))

def login():
    data = json.dumps({"username": "operator", "password": "testpass123"}).encode()
    req = urllib.request.Request(f"{BASE}/api/auth/login", data=data,
                                  headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())["access_token"]

def upload_image(material, image_path, token):
    boundary = "----TestBoundary12345"
    with open(image_path, "rb") as f:
        img_data = f.read()
    filename = os.path.basename(image_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}/api/{material}/inspect",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

token = login()
print("LOGIN: OK")

# Test steel upload
steel_img = os.path.join(ROOT, "vision", "test_images", "image1.jpeg")
print(f"\n[STEEL UPLOAD] image={steel_img}")
result, status = upload_image("steel", steel_img, token)
print(f"  HTTP {status}")
if status == 200:
    print(f"  inspection_id={result['inspection_id']}")
    print(f"  material={result['material']}")
    print(f"  total_defects={result['total_defects']}")
    print(f"  quality_score={result['quality_score']}")
    print(f"  severity={result['severity']}")
    print(f"  status={result['status']}")
    print(f"  detections={result['detections']}")
    print(f"  report_available={result['report_available']}")
else:
    print(f"  ERROR: {result}")

# Test metal upload
metal_img = os.path.join(ROOT, "vision", "test_images", "metal_test1.jpg")
print(f"\n[METAL UPLOAD] image={metal_img}")
result2, status2 = upload_image("metal", metal_img, token)
print(f"  HTTP {status2}")
if status2 == 200:
    print(f"  inspection_id={result2['inspection_id']}")
    print(f"  material={result2['material']}")
    print(f"  total_defects={result2['total_defects']}")
    print(f"  quality_score={result2['quality_score']}")
    print(f"  severity={result2['severity']}")
    print(f"  status={result2['status']}")
    print(f"  detections={result2['detections']}")
    print(f"  report_available={result2['report_available']}")
else:
    print(f"  ERROR: {result2}")

print("\nUPLOAD TESTS DONE")
