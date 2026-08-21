from app import create_app
from test_mfa_helper import login as mfa_login

app = create_app()
c = app.test_client()

mfa_login(c, "admin", "admin123")

REPORT_TYPES = [
    "Incident Summary Report",
    "Predictive Risk Assessment",
    "Patrol Deployment Plan",
    "Trend Analysis Report",
    "Settlement Compliance Report",
    "Comparative Period Report",
]

fails = []
for rt in REPORT_TYPES:
    for fmt in ("pdf", "excel"):
        r = c.post("/api/reports.php?action=generate",
                    json={"type": rt, "from": "2026-01-01", "to": "2026-08-16", "zone": "", "format": fmt})
        data = r.get_json()
        status = "OK" if r.status_code == 200 and data.get("ok") else "FAIL"
        print(f"{status:5} {rt:35} {fmt:6} -> {r.status_code} {data}")
        if status == "FAIL":
            fails.append((rt, fmt))
        elif r.status_code == 200:
            # actually download it to make sure the file is real and non-empty
            dr = c.get(f"/api/reports.php?action=download&file={data['file']}")
            ok = dr.status_code == 200 and len(dr.data) > 0
            print(f"      download check: {dr.status_code} bytes={len(dr.data)} {'OK' if ok else 'FAIL'}")
            if not ok:
                fails.append((rt, fmt, "download"))

print()
if fails:
    print("FAILURES:", fails)
else:
    print("ALL REPORT TYPE/FORMAT COMBOS PASSED")
