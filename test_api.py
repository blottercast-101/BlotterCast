from app import create_app
from test_mfa_helper import login as mfa_login

app = create_app()
client = app.test_client()

r = client.get("/login.html")
print("login.html:", r.status_code)

r = client.post("/api/auth.php?action=login", json={"username": "admin", "password": "wrong"})
print("bad login:", r.status_code, r.get_json())

r = client.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
print("password step (MFA code sent):", r.status_code, r.get_json())

result = mfa_login(client, "admin", "admin123")
print("otp verify (good login):", result)

r = client.get("/api/auth.php?action=me")
print("me:", r.status_code, r.get_json())

# create a census resident, then a blotter record referencing them
r = client.post("/api/documents.php?type=census", json={
    "lastName": "Cruz", "firstName": "Juan", "middleName": "Santos",
    "dob": "1990-05-01", "sex": "Male", "civilStatus": "Single",
    "address": "123 Rizal St", "householdNo": "HH-01", "contactNo": "0917-123-4567",
    "voterStatus": "Registered Voter", "occupation": "Farmer", "status": "Active",
})
print("create census:", r.status_code, r.get_json())
if r.status_code == 201:
    resident_id = r.get_json()["id"]
else:
    clist = client.get("/api/documents.php?type=census").get_json()
    resident_id = clist[0]["id"]

r = client.get("/api/documents.php?type=census")
print("list census count:", len(r.get_json()))

r = client.post("/api/records.php?type=blotter", json={
    "complainant": "Juan Cruz", "complainantId": resident_id,
    "respondent": "Pedro Reyes", "respondentAddr": "outside barangay",
    "nature": "Noise complaint", "type": "CIVIL", "status": "Pending",
    "zone": "Zone 1",
})
print("create blotter:", r.status_code, r.get_json())

r = client.post("/api/documents.php?type=clearance", json={
    "residentId": resident_id, "purpose": "Employment",
})
print("issue clearance:", r.status_code, r.get_json())

r = client.get(f"/api/documents.php?type=blotter_check&residentId={resident_id}")
print("blotter_check:", r.status_code, r.get_json())

r = client.get("/api/records.php?type=incidents&peek=1")
print("peek incident seq:", r.status_code, r.get_json())

r = client.get("/api/auth.php?action=logout")
print("logout:", r.status_code, r.get_json())

r = client.get("/api/records.php?type=incidents")
print("records after logout (should 401):", r.status_code, r.get_json())
