from fastapi.testclient import TestClient
from src.api.service import app

c = TestClient(app)

def test_status_endpoint_shape():
    r = c.get("/admin/train/status", headers={"X-Admin-Token":"changeme"})
    assert r.status_code == 200
    j = r.json()
    assert "runs" in j and isinstance(j["runs"], dict)
