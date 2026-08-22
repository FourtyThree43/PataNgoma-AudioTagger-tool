# PataNgoma AudioTagger

[![CI](https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

**PataNgoma** is a provider-agnostic audio metadata intelligence platform built for deterministic music library scanning, multi-provider aggregation (MusicBrainz, Deezer, Spotify), explainable matching, and safe transactional tagging with atomic rollbacks.

---

## ⚡ Core Philosophy: Determinism Before Intelligence

```text
Deterministic Metadata > Provider Metadata > Fuzzy Matching > AI Reasoning
```

PataNgoma treats audio libraries with a **Recovery-First** mindset:
1. **Plan / Apply Lifecycle**: Preview and validate proposed metadata diffs in structured JSON before committing changes.
2. **Reversible Mutations**: Automatic pre-mutation snapshots saved in an SQLite audit journal enable one-command `rollback`.
3. **Provable Integrity**: Post-mutation verification and SHA-256 checksum tracking ensure tags write accurately without file corruption.

---

## 🚀 Quickstart

### Prerequisites
PataNgoma requires **Python >= 3.10** and Astral **`uv`**.

```bash
# Clone repository
git clone https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool.git
cd PataNgoma-AudioTagger-tool

# Install dependencies and sync virtual environment
uv sync

# Run the CLI
uv run patangoma --help
```

---

## 🛠️ CLI Command Reference

### 1. Library Health & Scanning
```bash
# Scan a directory recursively and report health summary, missing tags & duplicates
uv run patangoma scan ~/Music

# Output library statistics in machine-readable JSON
uv run patangoma scan ~/Music --json
```

### 2. File Inspection
```bash
# Inspect audio tags and technical audio properties
uv run patangoma inspect song.mp3
```

### 3. Explainable Matching & Search
```bash
# Query metadata providers (MusicBrainz, Deezer, Spotify) with explainable confidence scoring
uv run patangoma match song.mp3 --provider musicbrainz
```

### 4. Safe Plan & Apply Workflow
```bash
# 1. Generate a deterministic change plan
uv run patangoma plan song.mp3 --provider musicbrainz -o plan.json

# 2. Simulate changes in dry-run mode
uv run patangoma apply plan.json --dry-run

# 3. Apply changes with automatic backup
uv run patangoma apply plan.json
```

### 5. Instant Rollback & Audit History
```bash
# List past metadata mutations
uv run patangoma history

# Rollback any previous operation by its Operation ID
uv run patangoma rollback <OPERATION_ID>
```

### 6. Diagnostics & Verification
```bash
# Run system and provider environment diagnostics
uv run patangoma doctor

# Verify audio files for tag integrity and corruption
uv run patangoma verify ~/Music
```

---

## 🏗️ Repository Architecture

```text
src/patangoma/
├── cli.py                  # CLI / TUI presentation layer (Click + Rich + InquirerPy)
├── domain/                 # Pure domain models (TrackMetadata, Candidate, TagPlan) & typed exceptions
├── matching/               # Explainable matching engine & similarity scorers
├── providers/              # Provider adapters (MusicBrainz, Deezer, Spotify) & registry
├── services/               # Application services (Scanner, Planner, AudioBackend, AuditJournal, Doctor)
└── legacy/                 # Backward-compatible utilities
```

For detailed architectural specifications and development guides:
- 📖 [ARCHITECTURE.md](ARCHITECTURE.md) — System boundaries, data flow, and invariants
- 🤖 [AGENTS.md](AGENTS.md) — AI agent guidance, rules, and commands
- 💻 [DEVELOPMENT.md](DEVELOPMENT.md) — Local setup, testing with synthetic audio fixtures
- 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution workflow and conventions

---

## 🧪 Testing & Code Quality

```bash
# Run 50+ unit, contract, and property-based tests
uv run pytest --cov=patangoma

# Run linter and formatter checks
uv run ruff check .
uv run ruff format --check .
```

---

## 📜 License

This project is licensed under the terms of the GNU General Public License v3.0.
