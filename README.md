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
- [`cli/`](cli/) — the `aifootprint-cli` command-line client: a thin wrapper around the Python SDK for terminals, shell scripts, and CI/CD. See its own `README.md` for a Quick Start.
- [`frontend/developer-console/`](frontend/developer-console/) — the authenticated developer console (React/TypeScript): connect an API key and browse Dashboard, Projects, Applications, API Keys, Usage, Compare, Benchmarks, and an API Explorer, all consuming the same REST API as the SDK. See its own `README.md` for setup and security architecture (ADR-012).
- [`frontend/public-site/`](frontend/public-site/) — the public, unauthenticated developer landing site (static HTML/CSS, no framework). Deployed on a separate origin from the console — see [ADR-0012](docs/adr/0012-public-developer-site-origin-and-security.md).
- [`docs/`](docs/) — product requirements, functional requirements, architecture decision records, methodology documentation, and [`docs/RELEASING.md`](docs/RELEASING.md) for SDK/CLI versioning and PyPI publishing.
- [`data/`](data/) — methodology reference data.

The backend is the sole source of truth for estimation, methodology, and
persistence; the SDK is a client of its REST API, nothing more.

## License

MIT — see [`LICENSE`](LICENSE). Applies to the SDK (`aifootprint`) and CLI
(`aifootprint-cli`) packages, which are the two components published to
PyPI; see [`docs/RELEASING.md`](docs/RELEASING.md) for current publication
status.
