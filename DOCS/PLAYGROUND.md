# What-If Playground UI

## Start API
make serve  # or docker compose up

## Start UI
cd ui
npm install
npm run dev
# open http://127.0.0.1:5173

## Use it
1) Pick a persona on the left. ✓ means an adapter exists.
2) Chat with the persona in the top middle panel.
3) Edit candidates and base context. Add scenarios.
4) Choose explain mode and optional pin name.
5) Click "Run simulate" to see per-scenario results, reasons, and deltas.

## Notes
- The UI calls your existing API; no extra backend endpoints were added beyond /catalog/copy_variants.
- CORS allows http://localhost:5173 by default (see CONFIGS/serve/api.yaml).
- Admin pin flows require VITE_ADMIN_TOKEN in ui/.env.development.
