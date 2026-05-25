# Contributing

Thanks for helping improve qmtclient.

qmtclient is a lightweight Python client SDK for remote qmtserver gateways. It is designed for strategy computers, servers, and laptops that do not have MiniQMT or `xtquant` installed.

## Project Boundary

- qmtclient does not connect to MiniQMT directly.
- qmtclient does not depend on `xtquant`.
- qmtclient does not bypass qmtserver token auth, RPC allowlists, transparent RPC settings, or trading guards.
- qmtclient owns the remote SDK, strategy helpers, fake clients, fixtures, event replay, and client-side compatibility notes.
- qmtserver owns MiniQMT connectivity, server APIs, RPC dispatch, WebSocket serving, trading guards, audit logs, metrics, and operations.

## Local Development

```powershell
uv sync
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
```

Use this command to format code:

```powershell
uv run ruff format .
```

## Python Support

qmtclient supports Python `>=3.10` and is tested on Python 3.10, 3.11, 3.12, 3.13, and 3.14 across Windows, macOS, and Linux.

Do not add a `<3.14` cap unless a real runtime dependency requires it and the compatibility docs are updated.

## Tests

Tests should use:

- `httpx.MockTransport` for HTTP behavior;
- fake WebSocket connections for event streaming;
- `FakeQmtClient` for strategy-level unit tests;
- JSON or JSONL fixtures for offline replay.

Tests must not require a live qmtserver, MiniQMT, `xtquant`, real account IDs, or real tokens.

## Documentation

Update `README.md` or the relevant file under `docs/` when changing user-visible behavior.

Useful docs:

- `docs/connection.md`: remote connection setup.
- `docs/strategy.md`: strategy-friendly facades.
- `docs/offline-testing.md`: fake clients, fixtures, and event replay.
- `docs/compatibility.md`: qmtclient/qmtserver API compatibility.
- `docs/release.md`: release readiness checklist.

## Security

Do not commit real tokens, account IDs, passwords, private keys, personal paths, MiniQMT userdata, market data, or logs.

Example values must be obviously fake, such as `example-token`, `example-account`, or `http://192.168.1.10:8000`.

## Commit Messages

Use Conventional Commits:

```text
type(scope): summary
```

Common types:

- `feat`: user-visible functionality.
- `fix`: bug fixes.
- `docs`: documentation changes.
- `test`: test additions or changes.
- `refactor`: behavior-preserving code restructuring.
- `style`: formatting-only changes.
- `chore`: tooling, dependency, configuration, or maintenance work.
- `ci`: continuous integration changes.

Examples:

```text
feat(strategy): add account facade
fix(events): preserve websocket query parameters
docs(connection): document vpn setup
ci(actions): add python matrix
```
