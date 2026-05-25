# AGENTS.md

This file defines project rules for automation agents and human collaborators working on qmtclient. Before changing code, read this file, then read `README.md`, `docs/README.md`, `docs/roadmap.md`, and the relevant source files.

## Project Goal

qmtclient is a standalone Python client SDK for remote qmtserver gateways. It runs on strategy computers, servers, and laptops that do not have MiniQMT or `xtquant` installed. It talks to qmtserver over HTTP RPC and WebSocket. qmtserver runs on a Windows gateway machine connected to MiniQMT.

Target architecture:

```text
strategy computer / server / laptop
  - qmtclient
  - no MiniQMT
  - no xtquant
        |
        | HTTP RPC / WebSocket / token
        |
MiniQMT gateway computer
  - qmtserver
  - MiniQMT
  - xtquant
```

## Project Boundary

- qmtclient must not connect to MiniQMT directly.
- qmtclient must not depend on `xtquant`; do not add it to runtime dependencies, test dependencies, or source imports.
- qmtclient must not bypass qmtserver token auth, RPC allowlists, transparent RPC switches, or trading guards.
- qmtclient must not implement a GUI.
- qmtclient owns the client SDK, strategy developer experience, fake client, fixtures, event replay, and client-side compatibility notes.
- qmtserver owns server APIs, RPC, WebSocket, security, trading protection, auditing, runtime behavior, and MiniQMT connectivity.

## Directory Rules

- Source code lives in `src/qmtclient/`.
- Tests live in `tests/`.
- Architecture notes, roadmap, milestone plans, and compatibility notes live in `docs/`.
- Example scripts live in `examples/`.
- The repository root should contain only entry documentation, configuration, lock files, and a small set of standard project files.
- Do not commit `.venv/`, cache directories, real tokens, real account IDs, MiniQMT user data, market data, or logs.
- Do not place qmtserver runtime artifacts or MiniQMT local paths in this repository.

## Development Commands

Common commands:

```powershell
uv sync
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

Use this command to format code:

```powershell
uv run ruff format .
```

Existing qmtclient tests should use `httpx.MockTransport`, fake WebSocket connections, fake clients, or fixtures. They must not require a real qmtserver, MiniQMT, or `xtquant`.

## Quality Gate

Before delivering or committing changes, run at least:

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

If an environment limitation prevents a check from running, state that clearly in the response. Do not use real tokens, real account IDs, or personal paths to make tests pass.

## Code Style

- Support Python `>=3.10`; do not add a `<3.14` cap unless the roadmap explicitly changes.
- Keep the `src/` layout; do not import source code from the repository root.
- Prefer the standard library and existing dependencies. New dependencies must have a clear purpose.
- Keep runtime dependencies lightweight. By default, qmtclient should only need HTTP/WebSocket client capabilities.
- Public APIs should return JSON-friendly base types such as `dict`, `list`, `str`, `int`, `float`, `bool`, and `None`.
- Public behavior must be covered by tests.
- Keep the base `QmtClient` small, stable, and compatible with qmtserver `/v1`.
- Split strategy facades, fake clients, fixture loading, and event replay by responsibility. Do not pile them into `client.py`.
- Trading-related client APIs should only organize client-side parameters and call server endpoints. They must not implement logic that bypasses server-side protection.

## Code Quality And Splitting

- Keep individual `.py` files under 300 lines when practical.
- When a `.py` file exceeds 400 lines, actively evaluate whether it should be split by responsibility.
- When a `.py` file exceeds 500 lines, split it unless it is generated code, a pure constants table, or a clearly justified central registry.
- Keep individual functions under 50 lines when practical.
- When a function exceeds 80 lines, prefer extracting private helpers, facade methods, or separate modules.
- When a test file exceeds 500 lines, split it by feature, for example `test_client.py`, `test_strategy.py`, `test_fixtures.py`, or `test_event_replay.py`.
- If nesting in one function goes beyond 3 levels, prefer early returns or helpers to reduce complexity.
- If one change mixes formatting, refactoring, features, and documentation, split it into smaller commits when possible.
- New public behavior must have tests. Trading-related changes must cover server rejection, RPC errors, or auth failure paths.

## Documentation Rules

- User-facing documentation should default to Chinese because qmt primarily targets mainland China users.
- Keep API names, module names, commands, error codes, and protocol names in their original spelling.
- Update `README.md` or the relevant file under `docs/` when adding user-visible behavior.
- Long-term planning belongs in `docs/roadmap.md`.
- Detailed single-milestone plans should live in standalone milestone documents.
- qmtclient/qmtserver compatibility notes should be documented from the client perspective under `docs/`.
- Collaboration rule changes belong in this file or `CONTRIBUTING.md`.

## Security Rules

- Do not write real account IDs, tokens, passwords, server addresses, or personal paths into the repository.
- Example tokens, accounts, and URLs must be obviously fake examples.
- Do not bypass qmtserver authentication, RPC allowlists, transparent RPC switches, or trading guards.
- Do not implement direct MiniQMT connectivity or direct `xtquant` calls in the client.
- Real trading capability must be explicitly configured, protected, and audited by qmtserver. qmtclient only expresses the client-side intent to call the server.

## Git Rules

- Do not revert changes the user did not ask you to revert.
- Do not commit `.venv/`, cache directories, or local runtime artifacts.
- Large files, logs, and MiniQMT data directories should stay ignored by `.gitignore`.
- Recommended branch names: `codex/<short-topic>`, `feature/<short-topic>`, `fix/<short-topic>`, or `docs/<short-topic>`.
- Commit messages should use Conventional Commits: `type(scope): summary`.
- The `summary` should be lowercase imperative English, have no trailing period, and preferably stay under 72 characters.
- Do not mix unrelated formatting, refactoring, features, and documentation in one commit when they can be split.
- Before committing, confirm `git diff --check` reports no whitespace errors.
- Unless explicitly requested, do not create commits for the user. Prepare the changes and report the verification results.

Commit types:

- `feat`: user-visible functionality.
- `fix`: bug fixes.
- `docs`: documentation changes.
- `test`: test additions or adjustments.
- `refactor`: behavior-preserving code structure changes.
- `style`: formatting or non-behavioral style changes only.
- `chore`: tooling, dependency, configuration, or maintenance tasks.
- `ci`: continuous integration changes.

Examples:

```text
feat(strategy): add market facade
docs(roadmap): add offline testing milestone
chore(tooling): configure ruff and ty
test(events): cover websocket event parsing
```
