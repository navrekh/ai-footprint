# Releasing the SDK and CLI

This document covers packaging, versioning, and publishing for the two
PyPI-distributed packages in this repository: the Python SDK (`aifootprint`,
in `sdk/`) and the CLI (`aifootprint-cli`, in `cli/`). It does not cover the
backend API or the developer console, neither of which is published to PyPI.

## Package identity

| Package | PyPI name | Import name | Source |
|---|---|---|---|
| SDK | `aifootprint` | `aifootprint` | `sdk/` |
| CLI | `aifootprint-cli` | `aifootprint_cli` | `cli/` |

## License

Both packages are MIT-licensed (see the repository root [`LICENSE`](../LICENSE),
mirrored into `sdk/LICENSE` and `cli/LICENSE` so each package's sdist is
self-contained when unpacked independently). `pyproject.toml` for both
packages declares `license = "MIT"` (SPDX expression) plus
`license-files = ["LICENSE"]`, the current packaging-metadata convention
(PEP 639, requires `setuptools>=77`, which both packages' `[build-system]`
now requires) — not the older, deprecated `license = { text = "..." }` table
form.

## Versioning policy

- The SDK and CLI version **independently**, each using Semantic Versioning
  (`MAJOR.MINOR.PATCH`).
- Both currently sit at `0.1.x` (a shared starting line, not a coupling
  requirement) and there is no reason to bump either as part of packaging
  work alone — only functional changes justify a version bump.
- Each package's version has exactly one source of truth, read dynamically
  by `pyproject.toml` (`[tool.setuptools.dynamic] version = { attr = ... }`)
  rather than duplicated in two places:
  - SDK: `sdk/aifootprint/__init__.py::__version__`
  - CLI: `cli/aifootprint_cli/__init__.py::__version__`
- **SDK/CLI compatibility constraint**: `cli/pyproject.toml` pins its SDK
  dependency to a compatible-release range,
  `aifootprint>=0.1.0,<0.2.0`. This means:
  - Installing the CLI always pulls a compatible SDK automatically — no
    separate "install the right SDK version" step for the end user.
  - A future SDK `0.2.0` (or `1.0.0`) cannot be silently pulled in by a CLI
    user's `pip install -U` until the CLI itself is updated to declare
    support for it (i.e., until `cli/pyproject.toml`'s constraint is
    deliberately widened as part of releasing a new CLI version that has
    been tested against that SDK version).
  - When the SDK's minor version changes in a way the CLI has verified it
    supports, update the upper bound in `cli/pyproject.toml`'s
    `dependencies` and cut a new CLI patch/minor release alongside it.

## Building

```bash
cd sdk && python -m build   # produces sdk/dist/aifootprint-<version>-py3-none-any.whl and .tar.gz
cd cli && python -m build   # produces cli/dist/aifootprint_cli-<version>-py3-none-any.whl and .tar.gz
```

Both are pure-Python, universal wheels (`py3-none-any`) — no compiled
extensions, no platform-specific builds needed.

Validate a build before publishing:

```bash
pip install twine
twine check dist/*
```

## Verifying a clean install (no repository, no editable install)

```bash
python -m venv /tmp/clean-check && source /tmp/clean-check/bin/activate
pip install --find-links sdk/dist --find-links cli/dist aifootprint-cli
aifootprint --help
aifootprint --version
deactivate
```

Once published, the same check works against the real index with a plain
`pip install aifootprint-cli` and no `--find-links` — this is exactly what
`.github/workflows/ci.yml`'s `cli-clean-install` job does on every push to
`main`, using the artifacts `sdk` and `cli` jobs just built (not anything
already on PyPI), so packaging regressions are caught before a release is
ever cut.

## CI

`.github/workflows/ci.yml` runs on every push to `main` and every pull
request: lint (`ruff`), type-check (`mypy`), unit tests (`pytest`), a wheel +
sdist build with `twine check`, and a clean-environment install-and-smoke-test
of the CLI using only the artifacts that build produced (never PyPI, never an
editable/repo-path install). It never publishes anything.

## Publishing (PyPI trusted publishing / OIDC)

Publishing is **tag-triggered only** — an ordinary push or merge to `main`
never publishes. Each package has its own release workflow and its own tag
prefix, so the SDK and CLI can be released independently:

| Package | Workflow | Tag pattern | Example |
|---|---|---|---|
| SDK | `.github/workflows/release-sdk.yml` | `sdk-v*.*.*` | `sdk-v0.1.0` |
| CLI | `.github/workflows/release-cli.yml` | `cli-v*.*.*` | `cli-v0.1.0` |

Each workflow:
1. Rebuilds and re-tests the package from source at that tag (lint, type
   check, unit tests) — never trusts a pre-built artifact from anywhere else.
2. Builds the wheel + sdist and runs `twine check`.
3. Scans the built artifact for anything that looks like a live AI Footprint
   API key (`afp_live_...` / `afp_test_...`) and fails the build rather than
   publish if one is found.
4. Verifies the git tag's version matches the package's own `__version__` —
   a mismatch fails the build before publish, so a tag can never
   accidentally publish the wrong version.
5. Only then, in a separate `publish` job gated by a GitHub Environment
   (`pypi-sdk-release` / `pypi-cli-release`), publishes to PyPI using
   [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish)
   with **OIDC trusted publishing** — `permissions: id-token: write` is the
   only credential-shaped thing in either workflow. **No PyPI API token, no
   long-lived secret, of any kind is configured or referenced anywhere in
   either workflow.**

### One-time setup required before either workflow can actually publish (not done as part of this change)

1. On PyPI, create the `aifootprint` and `aifootprint-cli` projects (first
   publish of a brand-new project name currently still needs one manual
   upload or PyPI's "pending publisher" flow — consult current PyPI docs at
   publish time, since this changes independently of this repository).
2. On each PyPI project's "Publishing" settings, add a trusted publisher
   pointing at this repository, the relevant workflow filename
   (`release-sdk.yml` / `release-cli.yml`), and the matching GitHub
   Environment name (`pypi-sdk-release` / `pypi-cli-release`).
3. In this GitHub repository's Settings → Environments, create the
   `pypi-sdk-release` and `pypi-cli-release` environments. Optionally add
   required reviewers to either environment for a manual approval gate
   before a publish job runs — this repository does not mandate that, it's
   an owner deployment-protection choice.
4. Tag and push, e.g. `git tag sdk-v0.1.0 && git push origin sdk-v0.1.0`, to
   trigger a real publish. **This has not been done as part of this
   implementation** — the workflows exist and are validated (YAML syntax,
   build/test steps run in CI on every push), but no tag has been pushed and
   no package has been published.

### Least privilege

Every job in every workflow declares only the GitHub token permissions it
needs (`contents: read` everywhere; `id-token: write` only in the `publish`
job, only for the OIDC handshake with PyPI). No workflow has write access to
repository contents, and no workflow publishes on any trigger other than its
own explicit tag pattern.

## Local development (unchanged)

For working on the SDK/CLI themselves (not distribution), the existing
editable-install workflow documented in `sdk/README.md` and `cli/README.md`
is unchanged:

```bash
cd sdk && pip install -e ".[dev]"
cd ../cli && pip install -e ".[dev]"
```
