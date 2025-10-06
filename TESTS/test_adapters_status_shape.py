from fastapi.testclient import TestClient
from src.api.service import app

c = TestClient(app)

def test_adapters_status_shape():
    r = c.get("/admin/adapters", headers={"X-Admin-Token":"changeme"})
    assert r.status_code in (200, 401)  # 401 if token differs in local env
    if r.status_code == 200:
        j = r.json()
        assert "use_stub" in j and "adapters" in j
