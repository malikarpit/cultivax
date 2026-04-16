from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

res = client.post("/api/v1/auth/register", json={
    "full_name": "Test P",
    "phone": "+918765411122",
    "password": "Test@12345",
    "role": "provider",
    "region": "Punjab"
})
print("Provider register status:", res.status_code)
if res.status_code == 201:
    data = res.json()["data"]
    print("User role:", data["user"]["role"])
    
    # decode token
    import jwt
    decoded = jwt.decode(data["access_token"], options={"verify_signature": False})
    print("Token role:", decoded.get("role"))
