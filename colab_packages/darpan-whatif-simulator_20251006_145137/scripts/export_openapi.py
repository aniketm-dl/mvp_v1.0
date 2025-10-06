from __future__ import annotations
from pathlib import Path
from fastapi.openapi.utils import get_openapi
from src.api.service import app
import json

def main():
    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        routes=app.routes,
        description="Darpan Labs What-If Simulator API"
    )
    out = Path("DOCS/openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(openapi_schema, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
