setup:
	pip install -e .

fmt:
	ruff --fix . || true
	black .
	isort .

lint:
	ruff .
	mypy .

test:
	pytest -q

gate:
	python scripts/eval_separation.py

guard:
	pytest TESTS/test_reason_guard.py -v

metrics:
	python scripts/eval_separation.py

all: test gate guard
	@echo "✅ All checks passed"

serve:
	uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000

openapi:
	python scripts/export_openapi.py

docker-build:
	docker build -t darpan/what-if-simulator:latest .

docker-run:
	docker compose up --build

postman:
	@echo "Open API/collections/what_if_simulator.postman_collection.json in Postman and set baseUrl/adminToken env."

pins:
	python scripts/cli.py pins --token changeme

pin_demo:
	python scripts/cli.py pin --name demo --weights '{"k0":0.5,"k1":0.5}' --token changeme

simulate_demo_pin:
	python scripts/cli.py simulate_pin --pin demo

lab-bank:
	python scripts/lab.py bank

lab-inspect:
	python scripts/lab.py inspect --twin k3

sft-synth:
	python scripts/prepare_llm_sft_data.py

sft-train-k3:
	python scripts/train_llm_persona_sft.py --twin_id k3

sft-eval-k3:
	python scripts/eval_llm_persona_sft.py --twin_id k3

opera-sft:
	python scripts/opera/prepare_sft_from_opera.py --cfg CONFIGS/opera/fields.yaml

train-all:
	python scripts/train_all_twins.py

train-status:
	curl -H "X-Admin-Token: changeme" http://127.0.0.1:8000/admin/train/status

ui:
	cd ui && npm install && npm run dev

ui-build:
	cd ui && npm install && npm run build && npm run preview

report-confusion:
	python scripts/reports/persona_confusion.py

report-deltas:
	python scripts/reports/scenario_delta_heatmap.py

persona-discover:
	python scripts/opera/discover_personas_from_opera.py --augment --min_rows 200 --max_personas 24

prep-ready:
	python scripts/pipeline/train_and_load_all_twins.py

reload-all:
	@python -c 'import json,http.client; from pathlib import Path; p=json.loads(Path("DATA/personas.json").read_text()); [print(t["id"], http.client.HTTPConnection("127.0.0.1",8000).request("POST",f"/admin/twin/{t[\"id\"]}/reload",headers={"X-Admin-Token":"changeme"}) or http.client.HTTPConnection("127.0.0.1",8000).getresponse().status) for t in p["personas"]]'

starter-ready:
	python scripts/starter_ready.py
