# ADR-0012: Public Developer Site — Origin and Security Boundary

## Status

Accepted. The separate-origin decision below was owner-approved, and the
concrete hostnames were resolved on 2026-09-21 (see "Resolved Hostnames").

## Context

Sprint 7A (PRD/FRD §40, approved in `b5bcbbb`) introduces a public,
unauthenticated developer-facing site that explains AI Footprint and links to
CLI installation, SDK documentation, API documentation, GitHub and the
Developer Console. PRD §40.14 and §40.21 item 3 require this decision to be
resolved via a dedicated ADR, "following the existing ADR-012 precedent,"
before implementation begins. This is that ADR.

The system already has exactly one precedent for a browser-based client:
[ADR-012](../ADR-012-console-authentication.md) established that the
authenticated Developer Console talks directly to the AI Footprint REST API
using a bearer API key held client-side (in-memory / `sessionStorage`, never
`localStorage`), with no BFF, no session layer, and a mandatory strict CSP as
the primary XSS control — because storage choice bounds *persistence*, not
*readability* while the page is open.

The public developer site is a **new, second browser-based surface**. It has
no legitimate reason to hold, request, or transmit an API key at all — it
exists to explain the product and drive developers toward CLI/SDK
installation or the console, not to make authenticated calls. Its risk
profile is therefore different in kind from the console's, not merely a
smaller version of it: the console's accepted risk (ADR-012) is "a real
credential is present in this page's origin"; the public site's target state
is "no credential is ever present in this page's origin at all," which
removes the console's core exposure category rather than bounding it.

Verified current state (inspection only, nothing built yet):
- `frontend/` contains exactly one application: `developer-console/` (React +
  TypeScript + Vite). There is no public-site directory today.
- The backend's CORS policy (`app/core/config.py::ALLOWED_ORIGINS`,
  `app/main.py::CORSMiddleware`) is an explicit, environment-driven allowlist
  with no wildcard — consistent with ADR-012's documented requirement.
- The console's `index.html` carries no CSP `<meta>` tag; ADR-012 treats CSP
  as mandatory for the console but (per its own "Deferred Work") did not
  implement it as part of that decision record. This ADR does not change
  that status for the console; it sets the requirement for the new public
  site's own build.
- No production hostname exists yet for either surface. This ADR
  deliberately does not invent one (per instruction) — it describes the
  boundary as a separate origin and leaves the concrete hostname to
  deployment configuration.

## Decision Drivers

- **Credential exposure**: the public site must never be a place an API key
  or session artifact could exist, not even briefly.
- **Blast-radius reduction**: a same-origin deployment means a single CSP
  misconfiguration, dependency compromise, or XSS bug on the marketing/docs
  surface (typically the highest-churn, most third-party-dependent part of a
  stack — analytics, embeds, docs tooling) becomes an attack surface against
  the console's origin and, therefore, the credential ADR-012 already
  accepted as a bounded risk there. Separating origins removes this
  cross-contamination path entirely rather than mitigating it.
- **Independent deployability**: PRD §40.12/§40.17 describe the public site
  as static, content-led, and roadmap-acknowledging; it should be able to
  ship, redeploy, and roll back on its own cadence without touching the
  console's build or release process.
- **Consistency with ADR-012**: this decision must not weaken or reinterpret
  ADR-012's console security model. The console's existing behavior,
  authentication flow, and CSP/CORS requirements are unchanged by this ADR.
- **PRD non-goals**: no new backend endpoints, no new authentication model,
  no redesign of the console (§40.19).

## Options Considered

### Option A — Same origin, separate route (e.g. `/`  marketing, `/console` app)

```text
example.com/           -> public site
example.com/console/*  -> authenticated Developer Console
```

A single origin serves both surfaces, routed by path.

- **Rejected.** A same-origin deployment means the public site's script
  execution context and the console's script execution context share (or
  can trivially be made to share, by a future change nobody intended as a
  security decision, e.g. a shared analytics snippet, a shared CDN script,
  or a relaxed CSP applied "for the whole site") the same origin boundary
  that browser same-origin policy uses to isolate `sessionStorage` and
  script access. ADR-012 already treats "a script running in the page's own
  origin can read `sessionStorage`" as the central risk it accepts for the
  console specifically because the console needs the key. The public site
  has no such need, so putting it in the same origin only imports risk
  without importing any requirement.
- Also weaker operationally: a public-site deploy and a console deploy would
  contend for the same release pipeline/rollback unit, contrary to PRD
  §40.12's framing of the public site as independently shippable.

### Option B — Separate origin (e.g. a marketing/docs domain or subdomain distinct from the console's origin)

```text
Public Developer Site                Authenticated Developer Console
(e.g. www.example.com                (e.g. console.example.com or an
 or a dedicated marketing domain —    entirely separate registered domain —
 hostname not yet selected)           hostname not yet selected)
        |                                       |
        | no credentials, no API calls          | Authorization: Bearer <API_KEY>
        | requiring authentication              | (ADR-012, unchanged)
        v                                       v
  (static content only;               AI Footprint REST API
   optional public, unauthenticated    (unchanged: API-key auth,
   endpoints only, e.g. docs           tenant isolation, CORS allowlist)
   search — none required for v1)
```

- Browser same-origin policy provides real, structural isolation between the
  two surfaces' script contexts, storage, and cookie jars — not a policy
  promise, a platform guarantee.
- A CSP bug, a compromised third-party script, or an XSS vector on the
  public site cannot read anything from the console's origin (and vice
  versa), because there is nothing to read across an origin boundary by
  default.
- The two surfaces can use different CSPs suited to their actual needs: the
  public site can allow whatever static-hosting/analytics resources it
  needs (subject to §"Security Requirements" below); the console keeps
  ADR-012's strict, credential-protecting CSP unchanged and undiluted by the
  public site's requirements.
- Independently deployable, independently rollback-able, consistent with
  PRD §40.12.
- Cost: two origins to configure (DNS/hosting) and, per PRD §40.15, a CORS
  policy that reflects the origin decision — this ADR requires the
  allowlist to *not* implicitly include the public site's origin, since the
  public site should have no reason to call authenticated endpoints.

## Decision

**Option B — separate origin.** The public developer site is deployed on an
origin distinct from the authenticated Developer Console's origin. This ADR
fixes that they are **not the same origin**, and that no code path may
assume otherwise. The exact hostnames were, at the time this decision was
first written, left to a later deployment-configuration step — they have
since been resolved by the owner; see "Resolved Hostnames" immediately
below.

This directly satisfies PRD §40.14 ("Sprint 7A does not assume both surfaces
must share the same origin") and §40.15's requirement that CORS/origin
separation preserve ADR-012's existing console security model "without
weakening it as a side effect of adding public pages."

## Resolved Hostnames

Owner-approved, 2026-09-21, after the production domain `aifootprint.tech`
was purchased. This resolves PRD §40.21 item 5 ("hosting/deployment target
... deferred to the ADR and implementation planning") for hostnames
specifically; the surfaces this ADR governs are the first two rows.

| Surface | Hostname | Status |
|---|---|---|
| Public Developer Site | `https://aifootprint.tech` | resolved (this ADR) |
| Authenticated Developer Console | `https://app.aifootprint.tech` | resolved (this ADR) |
| Developer API | `https://api.aifootprint.tech` | resolved (this ADR) |
| Documentation | `https://docs.aifootprint.tech` | resolved as a future subdomain; not deployed — no separate docs site exists in this repository, and none is created by this decision |

All four share the registered domain `aifootprint.tech` as distinct
subdomains (the public site sits at the apex/root), which satisfies this
ADR's separate-origin requirement: `aifootprint.tech`, `app.aifootprint.tech`
and `api.aifootprint.tech` are three distinct browser origins under the
same-origin policy (scheme + host + port), even though they share a
registrable domain. Nothing in this ADR required unrelated registered
domains — only that the console's origin differ from the public site's.

**This is a hostname decision, not an infrastructure decision.** DNS
records, TLS certificates, CDN/hosting configuration, load balancer
routing, and any other production-infrastructure provisioning for these
hostnames are a separate deployment step, not performed by this ADR and not
performed as part of resolving it. Purchasing the domain does not imply any
of that provisioning exists yet.

## Architecture

```text
Developer's Browser (public site)          Developer's Browser (console)
        |                                            |
        v                                            v
  Public Developer Site                    Developer Console
  (https://aifootprint.tech; static        (https://app.aifootprint.tech;
   content + optional public,               existing, ADR-012; Bearer
   unauthenticated API calls only,          <API_KEY>, held client-side
   e.g. the existing unauthenticated        per ADR-012's storage rules —
   POST /v1/organizations bootstrap,        unchanged)
   if/when the site chooses to offer
   an inline "get started" flow —
   not required for v1 and not
   assumed by this ADR)
        |                                            |
        | (no Authorization header                   | Authorization: Bearer <API_KEY>
        |  ever required to render                   |
        |  or use the public site)                    |
        v                                            v
               AI Footprint REST API  (https://api.aifootprint.tech;
                    unchanged: API-key auth, tenant isolation,
                    environment-driven CORS allowlist)
                              |
                              v
                         PostgreSQL
```

The public site has no server-side component of its own beyond static asset
hosting (consistent with PRD §40.12's "does not implement... hosting" — this
ADR specifies the boundary the eventual hosting choice must satisfy, not the
host itself).

## Trust Boundary

- The public site and the Developer Console **do not share trust
  assumptions**. Neither surface may assume the other's authentication
  state, storage, or script context is available to it.
- The public site **must not** read, write, or reference `sessionStorage`,
  `localStorage`, cookies, or any in-memory state belonging to the console's
  origin — and cannot, by construction, once the origins differ.
- The two surfaces **may link to each other** as ordinary cross-origin
  navigation (e.g. a "Go to Developer Console" call-to-action button/anchor
  linking to the console's origin). A normal `<a href>` navigation is not a
  trust relationship — no token, session, or state is passed in the link.
- If a future iteration wants a smoother handoff (e.g. pre-filling
  something on the console after a public-site click), that handoff must go
  through the console's own existing authenticated flow (the developer
  supplying/creating their own key inside the console, per ADR-012) — never
  through a URL parameter, `postMessage` of a credential, or any shared
  storage mechanism. This ADR does not design such a handoff; it forecloses
  the unsafe versions of it.

## Public Site Content Boundary

- The public site is documentation/marketing content: static text, code
  samples (installation commands, CLI/SDK usage snippets), and links. It
  requires **no authenticated API dependency** to load or function (PRD
  §40.14, §40.20 acceptance criteria).
- It **may** call the existing unauthenticated `POST /v1/organizations`
  bootstrap endpoint if a future iteration wants an inline "create your
  first API key" flow directly on the site — this is the same endpoint
  ADR-012 already documents as requiring no prior credential and fitting
  "API-only," "SDK," and "console" onboarding identically. This ADR permits
  that as an option; it does not require it, and Sprint 7A's initial
  implementation does not need to include it.
- The public site **must not** call, proxy, or embed any authenticated
  endpoint (anything requiring `Authorization: Bearer`), must not render any
  organization/project/application/usage data, and must not contain any
  API key — not a real one, not a placeholder that looks like a real format,
  and not one injected at build time as an environment variable baked into
  a static bundle (which would make it recoverable by anyone reading the
  shipped JS).
- Unless explicitly authorized otherwise (by the owner, at implementation
  time), the public site should be built from static/documentation
  resources only — no server-rendered dynamic content, no database access,
  no dependency on the backend beyond the one optional unauthenticated
  bootstrap call described above.

## CORS

- The backend's existing `ALLOWED_ORIGINS` allowlist (`app/core/config.py`,
  `app/main.py::CORSMiddleware`) governs which browser origins may call the
  API at all. This ADR does not change that mechanism.
- The public site's origin **should only be added to the allowlist if and
  when** the site actually calls the API (i.e., if the optional bootstrap
  flow above is implemented). Until then, the public site's origin has no
  reason to be present in `ALLOWED_ORIGINS` at all — a public-content site
  that never calls the API needs no CORS grant.
- If/when added, the grant is scoped to exactly the unauthenticated
  endpoint(s) the site uses in practice (CORS itself is per-origin, not
  per-endpoint, so this is enforced by the site's own code only calling
  what it needs — not by the CORS layer, which is a routing/transport
  concern, not an authorization one).
- `allow_credentials` remains `false` for this origin, identical to
  ADR-012's reasoning: no cookie-based auth exists anywhere in this system.
- No wildcard origin, ever, consistent with ADR-012 and the backend's
  existing policy.

## Content-Security-Policy

- The public site **must** ship its own CSP, scoped to what it actually
  needs (its content is simpler than the console's — mostly static
  text/code samples/links — so its CSP can likely be stricter than the
  console's, not looser).
- No third-party script should be added to the public site without explicit
  review; where one is unavoidable (e.g. analytics), it must be
  Subresource-Integrity-pinned or loaded from a reviewed, pinned source, and
  must not be granted access to anything resembling a credential (there is
  none to grant, by design — this is a defense-in-depth statement, not a
  mitigation for a risk that should exist).
- The public site's CSP is independent of the console's CSP (ADR-012). Nether
  site's CSP should be loosened to accommodate the other; they are unrelated
  configurations belonging to unrelated origins.

## Security Requirements

- No API key, session token, or credential of any kind in the public site's
  source, build output, environment-baked bundle, or served HTML/JS.
- No authenticated API call required for any public-site page to load or
  function.
- No reuse, reading, or writing of the console's storage (`sessionStorage`/
  `localStorage`) or cookies — structurally true once the origins differ,
  and must not be undone by a future same-origin embed (e.g. an `<iframe>`
  of the console inside the public site, or vice versa) without a fresh ADR.
- Links between the two surfaces are ordinary cross-origin navigation only —
  no token, key, or session artifact passed via URL, `postMessage`, or
  shared storage.
- The public site's CORS grant (if any) is added only for the specific
  unauthenticated endpoint(s) it actually calls, never a blanket grant.
- The console's existing behavior, CSP requirement, storage rules, and
  authentication flow (ADR-012) are **unchanged** by this decision. Nothing
  in this ADR modifies `AuthService`, `tenant_context.py`, or any backend
  authorization path.
- Deployment must support independent security controls per origin (its own
  CSP, its own CORS treatment, its own hosting/CDN configuration) — this
  ADR does not require a specific hosting provider or platform, only that
  whatever is chosen can express two origins with independently
  configurable security headers.

## Consequences

**Positive:**
- Structural (platform-enforced, not policy-enforced) isolation between a
  credential-bearing surface (console) and a content-only surface (public
  site) — the strongest available mitigation for the cross-contamination
  risk this ADR is about, and stronger than any CSP/code-review discipline
  alone could provide on a shared origin.
- The public site can adopt whatever static-hosting, CDN, analytics, or
  content-tooling choices best fit a marketing/docs surface without those
  choices ever becoming a console security review question.
- Independent deploy/rollback cadence for each surface, consistent with PRD
  §40.12.
- ADR-012's console security model is preserved exactly as decided —
  nothing about this ADR asks the console to change.

**Negative:**
- Two origins to provision, host, and secure instead of one — real,
  ongoing operational overhead (DNS, TLS, hosting config) versus Option A's
  single deployment unit.
- Any future "smoother" cross-surface UX (e.g. seamless handoff from public
  site to a pre-authenticated console state) requires deliberate design work
  through the console's existing auth flow rather than being free by virtue
  of shared origin — this is an accepted trade-off, not an oversight.

## Deferred Work

Explicitly deferred, not decided, and not implied by this ADR:
- ~~The concrete hostnames/domains for either origin~~ — resolved; see
  "Resolved Hostnames" above. What remains deferred is the actual
  provisioning behind those hostnames.
- DNS records, TLS certificates, CDN/hosting configuration, load-balancer
  routing, and any other production-infrastructure provisioning for
  `aifootprint.tech`, `app.aifootprint.tech`, `api.aifootprint.tech` and
  `docs.aifootprint.tech` — a deployment-time task, not performed by this
  ADR or by resolving the hostname decision.
- Implementation of the public site's CSP headers, CORS allowlist entry (if
  any), and hosting configuration — this ADR specifies the required policy
  shape, not the implementation, consistent with how ADR-012 treated CORS
  implementation as a separate task from the decision itself.
- Any inline "create your first API key" flow on the public site — permitted
  by this ADR, not required by it.
- Any cross-surface handoff UX beyond ordinary hyperlinks.

## Impact on Existing Systems

**Developer Console (ADR-012):** none. No change to its authentication
model, storage rules, CORS entry, or CSP requirement.

**Python SDK / CLI:** none. Neither is a browser client and neither is
affected by an origin decision that only concerns browser-based surfaces.

**Backend API:** no change required by this ADR alone. `ALLOWED_ORIGINS`
will need `https://app.aifootprint.tech` added once the console is actually
deployed there (unchanged mechanism — an environment-variable value, per
ADR-012 — not a code change to authorization logic), and gains, at most,
one further entry for `https://aifootprint.tech` if and only if the public
site later calls an unauthenticated endpoint. Neither addition is made by
this change; both are deployment-time configuration.
