# Documentation Index

This repository contains the Darpan Labs **OPeRA-SSR** MVP: a data-driven persona discovery and Semantic Similarity Rating system trained on the OPeRA dataset.  
Use the resources below to onboard quickly and dive deeper into each area of the stack.

## Core Guides

- [`README.md`](../README.md) – project overview and end‑to‑end workflow (local + AWS)
- [`QUICKSTART.md`](../QUICKSTART.md) – detailed local setup & training instructions
- [`QUICKSTART_AWS.md`](../QUICKSTART_AWS.md) – AWS workflow with cost notes and troubleshooting
- [`IMPLEMENTATION_SUMMARY.md`](../IMPLEMENTATION_SUMMARY.md) – technical deep dive of every subsystem
- [`AWS_SSR_TRAINING_GUIDE.md`](../AWS_SSR_TRAINING_GUIDE.md) – complete AWS provisioning & automation guide

## Reference Material

- [`docs/mvp_scope.md`](mvp_scope.md) – product scope and acceptance criteria
- [`docs/CREDENTIALS_GUIDE.md`](CREDENTIALS_GUIDE.md) – how to manage OpenAI + AWS credentials securely
- [`SSR_IMPLEMENTATION_GAP_ANALYSIS.md`](SSR_IMPLEMENTATION_GAP_ANALYSIS.md) – mapping between the SSR paper and this codebase
- [`CODEBASE_AUDIT_COMPREHENSIVE.md`](CODEBASE_AUDIT_COMPREHENSIVE.md) – historical cleanup notes and file retention decisions

## TODO / Open Design Items

- No production HTTP API is shipped yet. See [`docs/API.md`](API.md) for the latest design notes.
- Model versioning and subgroup fairness dashboards are not implemented; track progress in `IMPLEMENTATION_SUMMARY.md`.

> Looking for legacy LLM twin documentation? Everything has been archived under the `archive/` directory for historical reference. The active code path is fully SSR-based.
