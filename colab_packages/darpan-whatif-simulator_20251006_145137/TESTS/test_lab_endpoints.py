from fastapi.testclient import TestClient
from src.api.service import app

c = TestClient(app)

def test_bank_and_inspect():
    b = c.get("/twin/bank")
    assert b.status_code == 200
    twins = b.json()["twins"]
    assert isinstance(twins, list)
    if twins:
        tid = twins[0]["id"]
        r = c.get(f"/twin/{tid}/inspect")
        assert r.status_code == 200
