# Quickstart (hands-on)

1) API
   make setup
   make serve   # http://127.0.0.1:8000/health

2) Train personas from OPeRA (one command)
   make prep-ready
   # This: generates SFT from OPeRA, trains LoRA adapters for all personas in DATA/personas.json,
   # flips llm.use_stub:false, reloads adapters, and verifies chats.

3) Talk to ready twins
   make starter-ready
   # or open the UI: cd ui && npm install && npm run dev

4) Run full tests and gates
   make test && make gate
