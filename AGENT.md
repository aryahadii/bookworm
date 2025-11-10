# Bookworm Agent Playbook

This repository is a Django 2.2 project that wraps the Fidibo e-book API to download purchased titles, strip DRM, and return repackaged EPUB files. Use this guide whenever you work on automation tasks for the project.

## Mission Priorities
- **Correctness first:** confirm crypto, file, and network operations behave exactly as intended. Treat external API contracts as fragile; add guards for missing keys and unexpected payloads.
- **Security & privacy:** never persist or log usernames, passwords, session keys, or decrypted book content. Avoid introducing features that surface these values in URLs, HTML, or logs.
- **Reliability & idempotency:** downloading/patching EPUBs mutates the filesystem; make sure new logic is repeatable, cleans up temporary paths, and handles partially written files.
- **Performance & resource use:** book downloads can be large. Stream or chunk I/O, avoid loading entire archives into memory, and close descriptors promptly.
- **Testing & observability:** expand automated coverage beyond the current minimal `fidibo/tests.py`. For new code, provide deterministic unit tests and, when practical, integration tests using fixtures or mocked HTTP. Prefer Python logging over print statements.

## Repository Tour
- `bookworm/settings.py`: Django configuration plus Fidibo constants (`STORE_ID`, `APP_VERSION_NAME`, `DEVICE_INFO`, `BOOK_DOWNLOAD_PATH`). Changes here may affect API negotiation.
- `fidibo/api.py`: core client that encrypts/requests/decrypts Fidibo responses, downloads archives, removes DRM, and rebuilds EPUBs. Most edge cases (network retries, corrupt archives, AES padding) belong here.
- `fidibo/views.py`: request handlers that call into `FidiboConnection`, then stream the generated EPUB back to the browser. Sensitive data currently flows through URL params; patching this requires careful routing updates.
- `templates/`: Bootstrap-based UI for login, listing books, and triggering downloads.

## Local Environment
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `python manage.py migrate` (uses SQLite by default)
4. `python manage.py runserver 0.0.0.0:8000`

### Tests & Linters
- Run unit tests: `python manage.py test`
- Style checks: `flake8` (configure locally if needed); `yapf` is available but not enforced in CI.
- For cryptography-heavy changes, add regression tests with mocked AES inputs to prevent silent breakage.

## Implementation Guidelines
- **Networking:** centralize all Fidibo requests in `FidiboConnection`. Set explicit timeouts, add retry/backoff where justified, and handle HTTP errors gracefully (no silent failures). Mock `requests.get` in tests.
- **Filesystem:** prefer `pathlib` for new code, keep operations inside `settings.BOOK_DOWNLOAD_PATH`, and guarantee cleanup via context managers or `try/finally`.
- **Concurrency:** Django views may run in parallel. Guard shared directories, avoid predictable temporary names, and make functions re-entrant.
- **Crypto:** preserve padding/encoding semantics. Validate new keys or IVs with unit tests before committing.
- **Internationalization:** UI defaults to Persian locale; keep templates UTF-8 and do not hardcode English copy unless confirmed.

## Definition of Done Checklist
- Tests and linting pass locally.
- Sensitive information never logged or exposed.
- File writes are atomic/idempotent; temporary artifacts removed.
- Any new endpoints validate input, enforce CSRF where applicable, and use Django's URL reversing instead of manual string concatenation.
- Documentation (README/this file) updated when behavior or setup changes.

Keep changes focused and well justified. When in doubt, surface assumptions in your summary so reviewers can reason about trade-offs quickly.
