from app import create_app
from test_mfa_helper import login as mfa_login

app = create_app()
client = app.test_client()

mfa_login(client, "admin", "admin123")

# duplicate resident should be rejected
payload = {
    "lastName": "Dela Cruz", "firstName": "Maria", "dob": "1985-03-10", "sex": "Female",
    "address": "45 Mabini St", "householdNo": "HH-09",
}
r1 = client.post("/api/documents.php?type=census", json=payload)
r2 = client.post("/api/documents.php?type=census", json=payload)
print("first create:", r1.status_code, "duplicate create:", r2.status_code, r2.get_json())

# blotter with neither party a resident should be rejected
r = client.post("/api/records.php?type=blotter", json={
    "complainant": "Totally Random", "respondent": "Nobody Known",
    "nature": "Dispute", "type": "CIVIL",
})
print("blotter, no resident party:", r.status_code, r.get_json())

# same-person blotter should be rejected
resident_id = r1.get_json()["id"]
r = client.post("/api/records.php?type=blotter", json={
    "complainant": "Maria Dela Cruz", "complainantId": resident_id,
    "respondent": "Maria Dela Cruz", "respondentId": resident_id,
    "nature": "Dispute", "type": "CIVIL",
})
print("blotter, same person both sides:", r.status_code, r.get_json())

# switch to a Data Encoder (no edit/delete rights) and confirm 403 on PUT
client.get("/api/auth.php?action=logout")
mfa_login(client, "pencoder", "encoder123")
r = client.put("/api/records.php?type=incidents&id=1", json={"status": "Resolved"})
print("encoder PUT incidents (should 403):", r.status_code, r.get_json())

r = client.post("/api/documents.php?type=census", json={
    "lastName": "Reyes", "firstName": "Ana", "dob": "2000-01-01", "sex": "Female",
})
print("encoder can still add census (allowed):", r.status_code)
