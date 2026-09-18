# AI Footprint

AI Footprint estimates the resource impact (energy, water, CO2e) of AI
workloads — conversational, image, video, audio, coding and agentic — as
**ranges with confidence, evidence level and methodology version**, never
as a fabricated exact measurement.

- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) — first footprint estimate in about 10 minutes.
- [`docs/PRD.md`](docs/PRD.md) / [`docs/FRD.md`](docs/FRD.md) / [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) / [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — full product and technical specification.

## Repository layout

- [`backend/footprint-api/`](backend/footprint-api/) — the FastAPI backend: estimation engine, persistence, usage intelligence, and the REST API. See its own `README.md` for setup and the sprint-by-sprint delivery history.
- [`sdk/`](sdk/) — the official Python SDK (`aifootprint`): a thin, typed REST client with no estimation logic of its own. See its own `README.md` for a Quick Start.
- [`docs/`](docs/) — product requirements, functional requirements, architecture, and methodology documentation.
- [`data/`](data/) — methodology reference data.

The backend is the sole source of truth for estimation, methodology, and
persistence; the SDK is a client of its REST API, nothing more.
