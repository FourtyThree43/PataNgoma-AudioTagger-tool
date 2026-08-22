# AGENTS.md — AI Agent Development & Contribution Guide

This document contains authoritative rules, architectural constraints, and operating procedures for AI coding agents and human contributors working on **PataNgoma AudioTagger**.

---

## 1. Project Purpose & Scope

PataNgoma is a **provider-agnostic audio metadata intelligence platform** designed for:
- Deterministic music library scanning and inspection
- Multi-provider metadata aggregation (MusicBrainz, Spotify, Deezer, Discogs)
- Explainable matching and confidence scoring
- Safe, transactional metadata tagging with **Plan / Apply** workflows
- Dry-run validation, atomic backups, verification, and rollback

### Core Principle: Determinism Before Intelligence
```text
Deterministic Metadata > Provider Metadata > Fuzzy Matching > AI Reasoning
```
- AI may recommend and explain metadata changes.
- AI must **never** silently overwrite audio files without explicit user review or a validated plan.

---

## 2. Source-of-Truth & Repository Layout

- **`pyproject.toml` & `uv.lock`**: The single source of truth for runtime and development dependencies.
- **`src/patangoma/`**: The authoritative application package.
- **`tests/`**: Pytest test suite, including unit, integration, contract, and audio fixture tests.
- **`drafts/`**: Legacy exploratory code. **Do not import from or modify `drafts/` for production features.**

---

## 3. Canonical Developer Commands

Agents must use Astral `uv` for all environment management and tool execution:

```bash
# Synchronize virtual environment with lockfile
uv sync

# Run tests with coverage
uv run pytest
uv run pytest --cov=patangoma

# Linting & Formatting
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .
uv run ruff format --check .

# Run CLI application
uv run patangoma --help
uv run python -m patangoma.cli
```

---

## 4. Architectural Layer Boundaries

Every module belongs to a specific architectural layer with strict dependency directions:

```text
[ CLI / TUI Layer ] (patangoma.cli)
         │
         ▼
[ Application Services Layer ] (Plan/Apply, Scanner, Matcher, Tagger, Rollback)
         │
         ▼
[ Domain Layer ] (Pure models: TrackMetadata, MetadataCandidate, TagUpdate, MatchResult)
         ▲
         │
[ Provider Adapters ] (MusicBrainz, Spotify, Deezer protocols)
[ Storage & Audit ] (Cache, Backup history, SQLite store)
[ Filesystem / Audio Backend ] (Mutagen / MediaFile wrapper)
```

### Layer Rules & Invariants:
1. **Domain Models Must Be Pure**:
   - `TrackMetadata`, `MetadataCandidate`, and `TagUpdate` must NOT import or invoke CLI libraries (`click`, `InquirerPy`, `imgcat`, `rich`, `rgbprint`).
   - Domain models must NOT call `exit()`, `sys.exit()`, or print to standard output.
2. **Proper Error Handling**:
   - Never use blanket `except Exception: exit(1)` or silent suppression.
   - Raise explicit typed domain exceptions (e.g., `InvalidAudioFileError`, `ProviderUnavailableError`, `MetadataExtractionError`, `TagWriteError`).
   - The CLI layer is responsible for formatting exceptions into clear user messages and stable exit codes.
3. **Provider Isolation**:
   - All metadata providers must implement the standard `MetadataProvider` protocol.
   - Provider responses must be normalized into standard `MetadataCandidate` domain objects before reaching matching or tagging engines.
4. **Safety & Reversibility (Recovery-First)**:
   - Any operation that modifies files on disk must:
     1. Support `--dry-run`.
     2. Create a rollback backup/journal entry before mutating.
     3. Verify file integrity and checksum post-mutation.

---

## 5. Development & Contribution Workflow

When implementing features or bug fixes, agents must follow this sequential loop:

1. **Understand & Characterize**: Read the relevant modules and write characterization tests for existing behavior if modifying legacy logic.
2. **Smallest Safe Increment**: Make targeted, minimal changes respecting layer boundaries.
3. **Type & Lint**: Run `uv run ruff check .` and `uv run ruff format .`.
4. **Test**: Run `uv run pytest` and verify all tests pass.
5. **Verify Reversibility**: Ensure file mutations are logged and reversible.

---

## 6. Commit & Branching Conventions

- Use Conventional Commits:
  - `feat: add MusicBrainz provider candidate normalization`
  - `fix: prevent crash when track has missing year tag`
  - `test: add synthetic flac audio fixture test cases`
  - `refactor: extract pure TrackMetadata domain model`
  - `docs: update architecture overview in ARCHITECTURE.md`
- Branch naming: `feature/<name>`, `fix/<name>`, `refactor/<name>`.
