# Deploy

## Local
1) Build and run
   ```bash
   make docker-build
   docker compose up
   ```
2) Open http://127.0.0.1:8000/health
3) Export OpenAPI
   ```bash
   make openapi
   # -> DOCS/openapi.json
   ```

## Postman
- Import API/collections/what_if_simulator.postman_collection.json
- Set variables:
  - baseUrl = http://127.0.0.1:8000
  - adminToken = your admin token

## Config via env
- ADMIN_TOKEN overrides CONFIGS/serve/admin.yaml
- CORS_ALLOW_ORIGINS (comma-separated) overrides CONFIGS/serve/api.yaml
- RATE_LIMIT_REQS_PER_MIN sets the in-memory limiter

## Readiness
- /live for liveness, /ready for readiness
- /versions for model and serve flags

## Volumes
- Mount DATA and artifacts for persistence:
  - DATA/pins.json stores admin pins
  - artifacts holds policy heads and outputs

## Production Considerations
- Set strong ADMIN_TOKEN via environment variable
- Configure CORS_ALLOW_ORIGINS to only trusted domains
- Adjust RATE_LIMIT_REQS_PER_MIN based on expected traffic
- Use external Redis or similar for distributed rate limiting in multi-instance deployments
- Monitor /ready endpoint for health checks
- Logs include request IDs and latencies for tracing
