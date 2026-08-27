import urllib.request
import json

BASE = "http://127.0.0.1:8000"

def req(url, headers=None, data=None):
    r = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        ct = resp.headers.get("Content-Type", "")
        if "application/pdf" in ct:
            return {"_pdf_bytes": len(resp.read())}, resp.status
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read()), e.code
        except:
            return {"error": str(e)}, e.code

# Login
body, _ = req(f"{BASE}/api/auth/login",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"username": "operator", "password": "testpass123"}).encode())
token = body["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Get first steel inspection ID
body, _ = req(f"{BASE}/api/steel/inspections?page=1&limit=1", headers=h)
steel_id = body["items"][0]["inspection_id"]
print(f"[STEEL DETAIL] testing id={steel_id}")
detail, status = req(f"{BASE}/api/steel/inspections/{steel_id}", headers=h)
print(f"  status={status} id={detail.get('inspection_id')} score={detail.get('quality_score')} result={detail.get('status')}")

# Get first metal inspection ID
body, _ = req(f"{BASE}/api/metal/inspections?page=1&limit=1", headers=h)
metal_id = body["items"][0]["inspection_id"]
print(f"[METAL DETAIL] testing id={metal_id}")
detail, status = req(f"{BASE}/api/metal/inspections/{metal_id}", headers=h)
print(f"  status={status} id={detail.get('inspection_id')} score={detail.get('quality_score')} result={detail.get('status')} defects={detail.get('defects')}")

# Test steel report download
print(f"[STEEL REPORT] downloading for {steel_id}")
body, status = req(f"{BASE}/api/steel/reports/{steel_id}/download", headers=h)
print(f"  status={status} pdf_bytes={body.get('_pdf_bytes', body)}")

# Test metal report download (pick a known ID)
body2, _ = req(f"{BASE}/api/metal/inspections?page=1&limit=1", headers=h)
metal_id2 = body2["items"][0]["inspection_id"]
print(f"[METAL REPORT] downloading for {metal_id2}")
body3, status3 = req(f"{BASE}/api/metal/reports/{metal_id2}/download", headers=h)
print(f"  status={status3} pdf_bytes={body3.get('_pdf_bytes', body3)}")

# Test 404 on bad ID
body4, status4 = req(f"{BASE}/api/steel/inspections/FAKEID999", headers=h)
print(f"[404 TEST] status={status4} detail={body4.get('detail')}")

# Test steel filter by status
body5, status5 = req(f"{BASE}/api/steel/inspections?status=PASS", headers=h)
print(f"[STEEL FILTER PASS] status={status5} total={body5.get('total')}")

body6, status6 = req(f"{BASE}/api/metal/inspections?status=FAIL", headers=h)
print(f"[METAL FILTER FAIL] status={status6} total={body6.get('total')}")

print("\nALL DETAIL TESTS DONE")
