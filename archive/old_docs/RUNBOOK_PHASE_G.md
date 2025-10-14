# Phase G Runbook (Pins, Versions, Logging)

## Admin token
- Config: CONFIGS/serve/admin.yaml
- Send header: X-Admin-Token: <token>

## Create a pin
POST /admin/pin
{
  "name": "deal_fast_mix",
  "weights": {"k0":0.6, "k1":0.4},
  "conditioning": {"psychographic_tags":["thrift","speed_focus"]}
}

## List pins
GET /admin/pins  (admin header required)

## Delete a pin
DELETE /admin/pin/{name}  (admin header required)

## Use a pin in simulate
POST /simulate with "use_pin":"deal_fast_mix"
- Pin weights override mixture
- Pin conditioning overrides request conditioning

## Versions
GET /versions returns model/data versions and flags (heads loaded, cache stats)

## Logging
Each request logs: request_id, method, path, status, latency. Response carries X-Request-Id.

## CLI quickstart
python scripts/cli.py versions
python scripts/cli.py pin --name demo --weights '{"k0":0.5,"k1":0.5}' --token changeme
python scripts/cli.py pins --token changeme
python scripts/cli.py simulate_pin --pin demo
