import io

from app import create_app
from test_mfa_helper import login as mfa_login

app = create_app()
client = app.test_client()

mfa_login(client, "admin", "admin123")

# seed a bit of data to make analytics/reports non-empty
r = client.post("/api/documents.php?type=census", json={
    "lastName": "Cruz", "firstName": "Juan", "dob": "1990-05-01", "sex": "Male",
    "address": "123 Rizal St", "householdNo": "HH-01",
})
resident_id = r.get_json()["id"]

for i in range(3):
    client.post("/api/records.php?type=incidents", json={
        "date": "2026-08-10", "timeReported": "14:30", "zone": "Zone 1",
        "category": "Theft", "priority": "High", "status": "Under Investigation",
        "location": f"Test location {i}",
    })

r = client.post("/api/records.php?type=blotter", json={
    "complainant": "Juan Cruz", "complainantId": resident_id,
    "respondent": "Pedro Reyes", "nature": "Noise complaint", "type": "CIVIL",
})
blotter_id = r.get_json()["id"]

r = client.post("/api/records.php?type=settlements", json={"blotterId": blotter_id, "status": "Pending"})
print("create settlement:", r.status_code)

# ---- analytics ----
r = client.get("/api/analytics.php?action=dashboard")
print("dashboard:", r.status_code, r.get_json())

r = client.get("/api/analytics.php?action=zones")
print("zones count:", r.status_code, len(r.get_json()))

r = client.get("/api/analytics.php?action=heatmap")
print("heatmap:", r.status_code, len(r.get_json()))

r = client.get("/api/analytics.php?action=trends&year=2026")
print("trends:", r.status_code, r.get_json())

# ---- reports (PDF) ----
r = client.post("/api/reports.php?action=generate", json={
    "type": "Incident Summary Report", "from": "2026-01-01", "to": "2026-12-31", "format": "pdf",
})
print("generate PDF report:", r.status_code, r.get_json())
report_file = r.get_json().get("file")

r = client.get(f"/api/reports.php?action=download&file={report_file}")
print("download report:", r.status_code, r.content_type, "bytes:", len(r.data))

r = client.post("/api/reports.php?action=generate", json={
    "type": "Settlement Compliance Report", "format": "excel",
})
print("generate CSV report:", r.status_code, r.get_json())

r = client.get("/api/reports.php?action=list")
print("report list count:", r.status_code, len(r.get_json()))

# ---- exports (xlsx) ----
r = client.get("/api/exports.php?action=blotter_record")
print("export blotter_record xlsx:", r.status_code, r.content_type, "bytes:", len(r.data))

r = client.get("/api/exports.php?action=settlement_monitoring")
print("export settlement_monitoring xlsx:", r.status_code, "bytes:", len(r.data))

r = client.get("/api/exports.php?action=blotter_entry_2025")
print("export blotter_entry_2025 xlsx:", r.status_code, "bytes:", len(r.data))

# ---- users ----
r = client.get("/api/users.php?action=list")
print("users list:", r.status_code, len(r.get_json()))

r = client.post("/api/users.php?action=create", json={
    "username": "testuser1", "name": "Test User", "password": "testpass123", "role": "Desk Officer",
    "email": "testuser1@blottercast.local",
})
print("create user:", r.status_code, r.get_json())

r = client.get("/api/users.php?action=audit&limit=5")
print("audit log:", r.status_code, len(r.get_json()))

# ---- settings ----
r = client.get("/api/settings.php?action=list")
print("settings list keys:", r.status_code, len(r.get_json()))

r = client.post("/api/settings.php?action=save", json={"barangay_name": "Barangay Test Updated"})
print("save settings:", r.status_code, r.get_json())

r = client.post("/api/settings.php?action=backup")
print("run backup:", r.status_code, r.get_json())

r = client.get("/api/settings.php?action=backups")
print("backups list:", r.status_code, len(r.get_json()))

# ---- notifications ----
r = client.get("/api/notifications.php?action=list")
print("notifications list:", r.status_code, len(r.get_json()))

r = client.get("/api/notifications.php?action=unread_count")
print("unread count:", r.status_code, r.get_json())

# ---- blotter import (round-trip: export then re-import the same file) ----
r = client.get("/api/exports.php?action=blotter_record")
xlsx_bytes = r.data
r = client.post("/api/blotter_import.php", data={
    "file": (io.BytesIO(xlsx_bytes), "blotter-export.xlsx"),
}, content_type="multipart/form-data")
print("blotter import round-trip:", r.status_code, r.get_json())

# ---- ml proxy health (service likely not running, should degrade gracefully) ----
r = client.get("/api/ml_proxy.php?action=health")
print("ml health:", r.status_code, r.get_json())
