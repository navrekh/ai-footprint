# AI Footprint — Public Developer Site

The public, unauthenticated developer-facing site (Sprint 7A, PRD/FRD §40
Workstream B). It explains what AI Footprint is and links developers to CLI
installation, SDK documentation, API documentation, GitHub and the Developer
Console. It is **not** the [Developer Console](../developer-console/)
(`frontend/developer-console/`) and shares no code, build, deploy pipeline,
or trust boundary with it — see
[ADR-0012](../../docs/adr/0012-public-developer-site-origin-and-security.md)
for why.

## What this is

Static HTML + CSS. No JavaScript framework, no build step, no npm
dependencies, no bundler. This is a deliberate choice, not an oversight:

- The site's entire job is to render fixed marketing/documentation content
  and links — there is no interactive or stateful behavior that would
  justify a client-side framework.
- Zero JS dependencies means zero JS supply-chain surface and nothing that
  could accidentally end up bundling a secret into shipped code (there is no
  bundler step to leak one via).
- It keeps the site trivially auditable: `view-source:` on `index.html`
  shows the entire client-side behavior, which is none.

If a future iteration needs actual interactivity (e.g. a live "create your
first API key" flow calling the existing unauthenticated
`POST /v1/organizations` endpoint, which ADR-0012 explicitly permits), add
the smallest amount of vanilla JS or a lightweight bundler at that point —
don't adopt a framework preemptively.

## Local preview

Any static file server works, e.g.:

```bash
cd frontend/public-site
python3 -m http.server 8080
# open http://localhost:8080
```

## Required deployment configuration (not filled in here)

Two links in `index.html` are placeholders, marked `TODO(deploy)` in the
markup, because no production hostname has been selected yet
(PRD §40.21 item 5; ADR-0012 fixes only that these are **separate origins**,
not what those origins are named):

| Placeholder | Where | Replace with |
|---|---|---|
| `https://console.example.com` | nav CTA + footer | the real Developer Console origin |
| `https://api.example.com/docs` | footer | the real backend origin's `/docs` (FastAPI/Swagger UI) |

Do not point either placeholder at this site's own origin — see
ADR-0012's "Trust Boundary" section for why the two surfaces must not be
same-origin.

## Security boundary (ADR-0012 summary — read the ADR for the full reasoning)

- This site requires **no authentication and no API key** to load or
  function, and must never be given one.
- It must never read, write, or reference the Developer Console's
  `sessionStorage`/`localStorage`/cookies (structurally impossible once
  deployed to a different origin, per ADR-0012).
- Any third-party script (analytics, etc.) added later must be reviewed and
  either Subresource-Integrity-pinned or loaded from a pinned, reviewed
  source — none is included today.
- Links to the Developer Console are ordinary cross-origin navigation
  (`<a href>`) — no token, key, or session state is or should ever be
  passed through them.

## Content boundaries (PRD §40.16, enforced by review, not tooling)

- No claims of exact physical resource consumption — ranges, confidence,
  methodology version and provenance only.
- No rankings, "winner" designations, "greenest"/best-or-worst provider
  claims, scores, or leaderboards.
- Future integrations (provider/cloud/OpenTelemetry/application/browser/
  mobile — see [ADR-0011](../../docs/adr/0011-ai-workload-evidence-and-integration-architecture.md))
  are described as planned/roadmap only, never as already available.
