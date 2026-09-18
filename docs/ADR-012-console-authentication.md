# ADR-012: Developer Console Authentication

## Status

Proposed

## Context

AI Footprint's only authentication model today is a **bearer API key**: `Authorization: Bearer <API_KEY>`, resolved by `AuthService.authenticate()` to an organization and, optionally, a project. Verified directly in the repository:

- Raw keys are generated once (`app/core/security.py::generate_api_key`), returned to the caller exactly once (`ApiKeyCreated`, from `POST /v1/organizations` or `POST /v1/api-keys`), and never persisted — only a SHA-256 hash (`key_hash`) and a display-only prefix (`key_prefix`) are stored (`app/models/api_key.py`).
- Tenant/project isolation is enforced entirely in the service layer (`app/services/tenant_context.py`), independent of any notion of "who is asking" beyond the key itself.
- **There is no concept of a human user, account, login, password, or session anywhere in the domain model.** A repository-wide search (`grep -rln "class User\|class Session\|class Account\|class Login" app/`) matches nothing except an unrelated `AccountingBoundary` enum (methodology accounting boundaries A/B/C, not a login concept). The only identity primitives that exist are `Organization`, `Project`, and `ApiKey`.
- No CORS middleware exists anywhere in `app/main.py` or elsewhere (`grep -rn "CORSMiddleware\|cors" app/` returns nothing).
- FRD §36.13 states: *"the developer console must not bypass backend authorization — every console action goes through the same authenticated REST API a direct API caller would use."* This constrains the console's traffic to go through the real API, but does not by itself decide whether that traffic originates from the browser directly or via an intermediary.
- PRD's API Explorer description (§"Developer console and API Explorer") states the developer can *"provide/select an API key"* directly in the tool — evidence the product spec already anticipates a developer handling their own raw key within the console UI, at least for that feature.

The Developer Console is a new client of this API and, being browser-based, introduces a genuinely new class of credential-exposure risk (DevTools, extensions, XSS, persistent storage) that a server-side SDK does not have. This ADR exists because the FRD does not resolve *how* the console authenticates — only that it must go through the same backend authorization.

## Decision Drivers

- **Credential exposure**: what can see or exfiltrate an API key, and under what conditions.
- **Security**: does not weaken the existing API-key model; does not add a parallel authentication system with its own new attack surface unless justified.
- **Simplicity**: Sprint 5 is scoped as a "minimal developer console," not an enterprise platform.
- **Developer experience**: the console must remain fast to use and consistent with how the same developer already thinks about the API (a key, not a login).
- **Consistency with the existing API**: SDK and console should not need two different mental models for "how do I authenticate."
- **Sprint 5 scope**: explicit non-goals exclude RBAC, SSO, OAuth provider integrations, and enterprise IAM.
- **Operational complexity**: session infrastructure means session storage, expiry, CSRF handling, and a new deployable surface (a BFF), none of which exist today.
- **Future extensibility**: the decision should not foreclose a proper human-identity/session layer later, when it is actually justified (e.g., multi-person organizations, enterprise SSO).

## Options Considered

### Option A — Direct browser-to-API (bearer key in the browser)

```text
Developer
   |
   v
Developer Console
   |
   | Authorization: Bearer <API_KEY>
   v
AI Footprint REST API
   |
   v
PostgreSQL
```

The console is a static, client-side application. The developer supplies (or the console creates, via the existing `POST /v1/api-keys`) an API key, held in the browser for the duration of the session, and sent directly as a bearer token on every request — architecturally identical to what the Python SDK does, just from a browser instead of a process.

**Credential exposure, evaluated precisely — "not persisted in our backend" vs. "not exposed to the browser" are different properties:**
- The backend already guarantees the *first* property (no plaintext persistence server-side) regardless of which client is used. That guarantee is unaffected by Option A.
- Option A does **not** give the *second* property: the raw key necessarily lives in browser memory (and, if the console remembers it across reloads, in `sessionStorage`/`localStorage`) for as long as the developer is using the console. It is visible in DevTools' Network tab (as any bearer token sent over HTTPS is, for the user's own browser), and vulnerable to exfiltration by an XSS payload or a malicious/compromised browser extension with page-content access, exactly like any SPA holding a long-lived credential client-side (e.g. the well-known "SPA + long-lived API token" risk class).
- This risk is **materially reduced, not eliminated**, by three facts already true of this system: (1) API keys are individually revocable in one click (`POST /v1/api-keys/{id}/revoke`) with no other side effects; (2) keys can be **project-scoped**, so a console-specific key can be limited to exactly the project the developer is working in rather than a full-organization key; (3) nothing about this exposure is worse than the exposure already accepted for a `.env` file or shell history holding the same key for SDK/CLI use — the browser is a new *location* for the same credential, not a new *class* of credential.
- `localStorage` (persists across browser restarts) is a stricter *persistence* risk than `sessionStorage` (cleared when the tab/browser closes) or in-memory-only (cleared on reload) — but persistence and XSS-readability are different properties. **`sessionStorage` reduces how long a key survives; it does not reduce who can read it while the page is open.** Any script executing in the page's own origin — whether the application's own code, an injected XSS payload, or a compromised third-party dependency — has identical read access to `sessionStorage`, `localStorage`, and any in-memory JavaScript variable. None of these storage choices are isolated from the page's own script execution context. The choice among them is a console-implementation decision (recorded below), but it is a persistence-hardening choice, not an XSS mitigation.

**CORS**: required — a browser calling a different-origin API cannot function without it. Origins are limited to the console's own known hosts. `allow_credentials` is not needed, since authentication is a header (`Authorization`), not a cookie.

**Simplicity / deployment**: no new backend service, no new database table, no new dependency. The console is a static site; it can be deployed independently of the API.

**Consistency**: identical mental model and identical request shape to the SDK ("send your key, get your data"). A developer moving between the console's API Explorer and their own SDK code sees the same requests.

**Appropriateness for an MVP console**: high. This is the standard pattern for early-stage developer-tool consoles (many API-first products' "playground"/"dashboard" tools work exactly this way before a full user/account system exists).

### Option B — Backend-for-Frontend (BFF) / session architecture

```text
Developer
   |
   v
Developer Console
   |
   | authenticated web session
   v
Console BFF
   |
   | server-side API credential
   v
AI Footprint REST API
   |
   v
PostgreSQL
```

The browser never sees the raw API key; it authenticates to a new BFF via a session (cookie-based), and the BFF holds/uses the real API key server-side on the developer's behalf.

- **Session management**: requires a wholly new mechanism — there is no session/cookie/token-issuance code anywhere in this repository today. This alone is new infrastructure, not a reuse of anything existing.
- **Credential storage**: the BFF must store *something* to authenticate the human (a password hash, a magic-link token, or federation to a third-party identity provider) — and there is no `User`/`Account` entity anywhere in the schema to attach it to. Building this means creating a new domain concept and, almost certainly, a new database table — a real, non-trivial scope and migration, not a configuration change.
- **CSRF**: cookie-based sessions reintroduce CSRF as a concern that a pure bearer-token API does not have today; the BFF would need explicit CSRF protection.
- **XSS**: reduces (but does not eliminate) the *specific* risk of the raw upstream API key being read by an XSS payload, since the browser only ever holds a session cookie/token for the BFF, not the API key itself. It does not eliminate XSS as a category of risk — a compromised page can still act as the logged-in user via the session.
- **BFF attack surface**: the BFF is a brand-new backend service (or a new module within one) that becomes a high-value target — it holds real API credentials for potentially every console user's organization. This is new attack surface, not a reduction of the total attack surface, even though it changes *where* the sensitive credential lives.
- **Additional backend endpoints**: login, logout, session-refresh, and proxy routes for every API call the console needs to make — a nontrivial new surface requiring its own tests and security review.
- **Deployment/operational complexity**: a new deployable service, session store (in-memory is not viable for more than a single instance; a persistent or shared session store is realistically required), and its own monitoring.
- **Second authentication model**: this is the central concern. The system would now have two independent authentication systems — API keys for machine/SDK use, and sessions for the console — with two different security postures to maintain, test, and reason about, for a "minimal developer console."
- **Conflict with Sprint 5 scope**: the PRD frames Sprint 5 as producing a *"minimal developer console... prioritizing developer onboarding and API usability over enterprise analytics."* A session/login system is a meaningful step toward exactly the enterprise-identity territory (SSO, RBAC, IAM) the non-goals list explicitly excludes, even though it is not literally OAuth or SSO.
- **Database changes**: effectively required (a user/account/session store), which was not anticipated anywhere in Sprint 1–5's PRD/FRD.
- **New infrastructure**: at minimum, a new deployable BFF service and a session-storage mechanism.

Verdict: **not automatically safer** — it trades "raw key briefly visible in a developer's own browser" for "a new backend service holding every console user's real API key, protected by a newly-built, unaudited session/login system with no existing precedent in this codebase." For a minimal Sprint 5 console, the BFF's own attack surface and scope are harder to justify than the risk it removes.

### Option C — Human-auth + BFF separation (dedicated session layer, API stays key-based)

```text
Developer Console
       |
       v
Dedicated web authentication/session
       |
       v
Developer Console backend/BFF
       |
       v
Existing AI Footprint API
```

This is the architecturally "correct" end state for a mature product: human identity and session management are cleanly separated from machine/API authentication, and the existing API is untouched. It is Option B's architecture stated as a deliberate long-term target rather than an ad hoc proxy.

Every objection to Option B applies here with equal force, because Option C **is** Option B's architecture — the difference is intent (durable design vs. quick proxy), not risk profile. It still requires a new user/session domain concept that does not exist today, a new deployable service, and materially expands Sprint 5's scope into identity infrastructure. It is the right direction for a **later, dedicated Enterprise/Auth sprint** (the PRD's own roadmap already reserves "Phase 5 — Enterprise: ... SSO, RBAC and gateway" for exactly this kind of work) — not for Sprint 5's "minimal console."

## Decision

**Option A — direct browser-to-API using the existing bearer API-key model.** The console authenticates to the API exactly as the Python SDK and any other API client does: the developer's own API key, sent as `Authorization: Bearer <API_KEY>` directly from the browser. No BFF, no session layer, no new authentication model, and no new backend infrastructure are introduced in Sprint 5.

This is the only option that requires zero new backend concepts, matches the existing "minimal console" scope in the PRD, and does not edge toward the explicitly-deferred RBAC/SSO/identity territory. Its residual risk (a credential visible in a developer's own browser while they use a developer tool) is real but bounded, well-precedented for MVP-stage developer consoles, and mitigated by capabilities the backend already has today (revocation, project-scoped keys) rather than by anything new.

## Architecture

```text
Developer's Browser
   |
   |  Authorization: Bearer <API_KEY>   (same header shape as the SDK)
   v
AI Footprint REST API  (unchanged: API-key auth, tenant isolation, request-ID middleware)
   |
   v
PostgreSQL
```

The console is a static, independently-deployed client application. It has no server-side component of its own beyond static asset hosting, and no privileged access path into the API that a direct API/SDK caller does not also have.

## Credential Handling

**Where the key lives:** the raw API key exists only in the developer's own browser, for the duration of their console session. It is never sent anywhere except as the `Authorization` header of a request to the AI Footprint API itself.

**Browser storage — persistence vs. protection (these are not the same property):**
- The console should hold the key in memory and, at most, `sessionStorage` (cleared when the tab/browser closes) — never `localStorage`, which persists indefinitely and would leave a key readable on a shared or public machine long after the developer's session ended.
- This is a **persistence** control only. It reduces *how long* a key remains recoverable on disk/in the browser profile. It does **not** reduce *who can read the key while the console tab is open* — a script running in the page's own origin (the application's own code, an XSS payload, or a compromised dependency) can read `sessionStorage`, `localStorage`, or an in-memory variable equally. **`sessionStorage` must not be described or treated as making the API key "secure" — it only limits exposure duration, not exposure scope.**
- Consequently, choosing direct browser-to-API authentication is an explicit, accepted **bounded bearer-token exposure risk**: for as long as the console tab is open with a valid key, a successful XSS attack against that page could read and exfiltrate it. This ADR does not claim otherwise. The risk is bounded — by revocability, by project-scoping, and by the key not surviving the browser session — not eliminated.
- Because storage choice cannot substitute for preventing script injection in the first place, **strict XSS protection is a mandatory requirement for the console implementation**, not optional hardening: a restrictive Content-Security-Policy (no `unsafe-inline`/`unsafe-eval` where avoidable), output encoding of all user/API-derived content rendered into the DOM, dependency review for the console's own third-party packages, and Subresource Integrity where third-party scripts are unavoidable. These are prerequisites for adopting this architecture, not follow-up nice-to-haves.

**Mandatory, non-negotiable handling rules:**
- The key **must never be placed in a URL** — not a query string, path segment, or fragment. URLs are captured by browser history, proxy logs, load balancer logs, and referrer headers far more readily than an `Authorization` header; a key in a URL is a strictly worse exposure than the header-based bearer token this decision already accepts.
- The key **must never be logged** — not in browser console output, not in any client-side analytics/error-reporting integration, and not in any server-side access log.
- The key **must never be persisted server-side in plaintext** — unchanged from today: only a SHA-256 hash and display prefix are ever stored (`app/models/api_key.py`), regardless of which client created or used the key.
- A raw key **must never be redisplayed after its one-time creation response** — the console has no more ability to retrieve it later than any other API client does, because the backend itself no longer has it to give back (`ApiKeyCreated` is returned exactly once).
- Every console request is authenticated **exactly like an SDK request**: a bearer header, validated by the existing, unmodified `AuthService`/`get_auth_context` path. There is no console-specific authorization branch anywhere in the backend, now or as a result of this decision.

**Recommended (product/UX, not backend) mitigation:** the console should default to *creating a new, project-scoped key for itself* (via the existing `POST /v1/api-keys`) rather than prompting the developer to paste an existing organization-level key, and should warn against pasting a production/shared key into a browser tool. This uses only existing backend capability and further bounds the blast radius of the accepted exposure above.

## CORS

CORS is **required** for Option A and does not exist today — this ADR documents the required policy; it does **not** implement it (per this task's explicit constraint).

- **Origins**: an explicit allowlist per environment (e.g. `http://localhost:<console-dev-port>` for local development, a staging console origin, and a production console origin) — never a wildcard (`*`). A wildcard is a materially weaker posture than necessary here specifically because the browser is holding a bearer credential; restricting origins limits which pages can even attempt a cross-origin call that a developer's browser might otherwise complete.
- **`allow_credentials`**: **not required**, and should be left `false`. Authentication is via the `Authorization` header, not cookies — this is a deliberate, positive consequence of choosing Option A over Option B, since cookie-based credentialed CORS carries CSRF implications that a bearer-header model does not.
- **Allowed methods/headers**: limited to what the console actually needs (`GET`, `POST`, `PATCH`, plus `OPTIONS` for preflight), and `Authorization`/`Content-Type` as allowed request headers — no broad `allow_headers=["*"]`.
- **Configuration**: origins should be environment-driven (a new setting, e.g. `ALLOWED_ORIGINS`, read per `ENVIRONMENT`), consistent with the existing `Settings` pattern in `app/core/config.py` — not hard-coded.

## Security Requirements

- No change to `AuthService`, `tenant_context.py`, API-key hashing, or any existing isolation rule — all remain exactly as they are today.
- CORS origins must be an explicit allowlist, never a wildcard, and must not enable credentialed (cookie) requests.
- The console must not introduce any code path that reaches the database, the estimation engine, or any internal service other than through the public REST API.
- **A strict Content-Security-Policy and other XSS mitigations (output encoding, dependency review, Subresource Integrity for any third-party script) are mandatory for the console build.** This is the primary control, since browser storage choice (`sessionStorage` vs. `localStorage`) only bounds how long a key persists, not whether a successful script-injection attack can read it while the page is open — storage choice must never be treated as a substitute for XSS prevention.
- The key must never appear in a URL (query string, path, or fragment) at any point in the console's request construction or navigation.
- The console's own security review (Sprint 5E, per the prior audit's implementation plan) must specifically verify: no key appears in browser storage beyond the agreed scope (`sessionStorage`, never `localStorage`), no key appears in any URL, no key appears in any client-side log or third-party script/analytics integration, and the CSP is actually enforced (not merely documented).
- Revocation remains the primary incident-response mechanism for a leaked console-origin key — no new mechanism is introduced or needed, since `POST /v1/api-keys/{id}/revoke` already exists and is sufficient.

## Impact on Python SDK

**None.** The SDK's authentication model is unchanged and unaffected by this decision: `Python Application --(API Key)--> AI Footprint REST API`, exactly as already specified. The SDK does not call, depend on, or need awareness of the console or this decision in any way.

## Impact on Quick Start

None of the Quick Start's steps (*Sign up → Create organization → Create project → Create application → Create API key → Send first workload → Receive footprint*) change as a result of this decision, and the existing unauthenticated bootstrap endpoint `POST /v1/organizations` is unaffected and unchanged.

That endpoint fits all three onboarding paths identically, since none of them require a different backend behavior:
- **API-only onboarding**: a developer calls `POST /v1/organizations` directly (e.g. via `curl`) to get an org, default project, and first API key in one call, then proceeds with raw HTTP or the SDK.
- **SDK onboarding**: the SDK could offer a thin wrapper over the same call (e.g. `AI.signup(name=...)`), but this is optional SDK convenience, not a new backend requirement.
- **Console onboarding**: the console calls the same public, unauthenticated endpoint from the browser (it requires no prior credential by design) to bootstrap the developer's first organization/project/key, then immediately holds the returned key in the browser exactly as described above for all subsequent calls.

No behavior of `POST /v1/organizations` changes.

## Consequences

**Positive:**
- Zero new backend infrastructure, endpoints, dependencies, or database changes.
- One authentication model across SDK, console, and any future first-party or third-party API client — lower total system complexity.
- Console can be built, deployed, and iterated on entirely independently of the API's release cycle.
- Fully consistent with Sprint 5's "minimal developer console" scope and explicit non-goals (no RBAC/SSO/OAuth/enterprise IAM introduced).
- Every existing security guarantee (hash-only storage, creation-time-only display, revocation, tenant isolation) is preserved unchanged, since the console is not a special case anywhere in the backend.

**Negative:**
- The developer's raw API key is present in their own browser's memory/`sessionStorage` while using the console — a real, non-zero exposure to XSS or a malicious browser extension, not eliminated (only bounded) by this decision.
- No human-level audit trail ("which person on the team did this") is possible — the system only knows "this API key," not "this person," which is an inherent limitation of not having a user/session model, not something this decision worsens.
- If the organization later needs per-person accountability, seat management, or enterprise SSO, that will require the Option C architecture as a **separate, later initiative** — this decision explicitly does not build toward it and some of the console's UI assumptions (e.g., "the browser directly holds a key") would need revisiting at that point.

## Deferred Work

Explicitly deferred, not built now, and not implied by this decision:
- Any human user/account/session/login model.
- A Backend-for-Frontend service of any kind.
- OAuth, SSO, RBAC, or enterprise identity federation.
- Per-person audit trails or seat-based access control.
- CORS implementation itself (this ADR documents the required policy only; implementing `CORSMiddleware` and the origin allowlist is a Sprint 5A implementation task, not part of this decision record).

These remain natural candidates for a future, dedicated Enterprise/Auth sprint, consistent with the PRD's existing "Phase 5 — Enterprise" roadmap entry (advanced organization management, analytics, reporting, SSO, RBAC and gateway) — not Sprint 5.
