import urllib.request
import json
import sys

BASE = "http://127.0.0.1:8000"

def req(url, headers=None, data=None):
    r = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# 1. Health
body, status = req(f"{BASE}/health")
print(f"[HEALTH] {status}: status={body['status']} steel_db={body['database_steel']} metal_db={body['database_metal']} steel_model={body['models']['steel']} metal_model={body['models']['metal']}")

# 2. Login
body, status = req(f"{BASE}/api/auth/login",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"username": "operator", "password": "testpass123"}).encode())
print(f"[LOGIN] {status}: username={body.get('username')} role={body.get('role')}")
token = body.get("access_token", "")
if not token:
    print("FATAL: no token, stopping")
    sys.exit(1)

h = {"Authorization": f"Bearer {token}"}

# 3. Wrong password
body2, status2 = req(f"{BASE}/api/auth/login",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"username": "operator", "password": "wrongpass"}).encode())
print(f"[LOGIN WRONG PW] {status2}: detail={body2.get('detail')}")

# 4. Steel inspections
body, status = req(f"{BASE}/api/steel/inspections?page=1&limit=5", headers=h)
print(f"[STEEL INSPECTIONS] {status}: total={body.get('total')} items={len(body.get('items',[]))}")

# 5. Steel analytics
body, status = req(f"{BASE}/api/steel/analytics", headers=h)
print(f"[STEEL ANALYTICS] {status}: total={body.get('total_inspections')} pass={body.get('pass_count')} fail={body.get('fail_count')} rework={body.get('rework_count')} score={body.get('avg_quality_score')} defects={body.get('total_defects')}")
print(f"  status_dist={body.get('status_distribution')}")
print(f"  defect_dist={body.get('defect_distribution')}")
print(f"  daily_volume count={len(body.get('daily_volume',[]))}")
print(f"  quality_trend count={len(body.get('quality_trend',[]))}")

# 6. Metal inspections
body, status = req(f"{BASE}/api/metal/inspections?page=1&limit=5", headers=h)
print(f"[METAL INSPECTIONS] {status}: total={body.get('total')} items={len(body.get('items',[]))}")

# 7. Metal analytics
body, status = req(f"{BASE}/api/metal/analytics", headers=h)
print(f"[METAL ANALYTICS] {status}: total={body.get('total_inspections')} pass={body.get('pass_count')} fail={body.get('fail_count')} rework={body.get('rework_count')} score={body.get('avg_quality_score')} defects={body.get('total_defects')}")
print(f"  status_dist={body.get('status_distribution')}")
print(f"  defect_dist={body.get('defect_distribution')}")
print(f"  daily_volume count={len(body.get('daily_volume',[]))}")

# 8. Steel reports list
body, status = req(f"{BASE}/api/steel/reports", headers=h)
print(f"[STEEL REPORTS] {status}: count={len(body) if isinstance(body,list) else body}")

# 9. Metal reports list
body, status = req(f"{BASE}/api/metal/reports", headers=h)
print(f"[METAL REPORTS] {status}: count={len(body) if isinstance(body,list) else body}")

# 10. Protected endpoint without token
body, status = req(f"{BASE}/api/steel/analytics")
print(f"[NO AUTH] {status}: detail={body.get('detail')}")

print("\nALL TESTS DONE")
