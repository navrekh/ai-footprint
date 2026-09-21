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

## Production hostnames (resolved)

Owner-approved, 2026-09-21 — see ADR-0012's "Resolved Hostnames" section:

| Surface | Hostname |
|---|---|
| This site | `https://aifootprint.tech` |
| Developer Console | `https://app.aifootprint.tech` |
| Developer API | `https://api.aifootprint.tech` |
| Documentation | `https://docs.aifootprint.tech` (future; no separate docs deployment exists yet) |

`index.html` already links to the Console and API origins above. **This is
a hostname decision, not infrastructure**: DNS, TLS, CDN and hosting
configuration for these domains are a separate deployment step, not
performed by this repository. Until that provisioning exists, these are
correct target URLs that do not yet resolve to a live deployment.

Do not point this site's own links at its own origin — see ADR-0012's
"Trust Boundary" section for why the site and the console must not be
same-origin (they aren't: `aifootprint.tech` and `app.aifootprint.tech` are
distinct origins under the same-origin policy even though they share a
registrable domain).

## Security boundary (ADR-0012 summary — read the ADR for the full reasoning)

- This site requires **no authentication and no API key** to load or
  function, and must never be given one. Where a code sample needs to show
  an API key variable, it uses an unmistakable placeholder
  (`<YOUR_API_KEY>`) — never a string shaped like a real key prefix
  (`afp_live_`/`afp_test_`), even as a placeholder, since the prefix format
  itself is sensitive to document verbatim next to a "paste your key here"
  example. CI's `public-site` job greps for that prefix and fails the build
  if it ever reappears, in any form.
- It must never read, write, or reference the Developer Console's
  `sessionStorage`/`localStorage`/cookies (structurally impossible once
  deployed to a different origin, per ADR-0012).
- Any third-party script (analytics, etc.) added later must be reviewed and
  either Subresource-Integrity-pinned or loaded from a pinned, reviewed
  source — none is included today.
- Links to the Developer Console are ordinary cross-origin navigation
  (`<a href>`) — no token, key, or session state is or should ever be
  passed through them.

### Content-Security-Policy

`index.html` ships a `<meta http-equiv="Content-Security-Policy">` tag,
default-deny with only the one resource this page actually loads
(`styles.css`, same-origin) allowed back in:

```
default-src 'none'; style-src 'self'; script-src 'none'; object-src 'none';
base-uri 'none'; form-action 'none'; upgrade-insecure-requests
```

No third-party script or style origin is allowed. Ordinary `<a href>`
navigation to other origins (GitHub, the Developer Console, API docs) is
unaffected — CSP does not govern link navigation, only resource loading.

**One directive can't be set this way**: `frame-ancestors` (clickjacking
protection — who may embed this page in an `<iframe>`) is explicitly
excluded from the `<meta>` CSP delivery mechanism by the CSP spec; browsers
silently ignore it there. Once this site has real hosting, the deployment
should also send a `Content-Security-Policy` **HTTP response header**
(not just the meta tag) including `frame-ancestors 'none'` — most static
hosts/CDNs support adding custom response headers. This is a hosting
configuration step, not something a static HTML file can express, so it is
not done in this repository.

## Content boundaries (PRD §40.16, enforced by review, not tooling)

- No claims of exact physical resource consumption — ranges, confidence,
  methodology version and provenance only.
- No rankings, "winner" designations, "greenest"/best-or-worst provider
  claims, scores, or leaderboards.
- Future integrations (provider/cloud/OpenTelemetry/application/browser/
  mobile — see [ADR-0011](../../docs/adr/0011-ai-workload-evidence-and-integration-architecture.md))
  are described as planned/roadmap only, never as already available.
