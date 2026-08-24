# PataNgoma AudioTagger

[![CI](https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue)](https://www.python.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

**PataNgoma** is a provider-agnostic audio metadata intelligence platform built for deterministic music library scanning, multi-provider aggregation (MusicBrainz, iTunes, Spotify, Deezer, Discogs, AcoustID, Lyrics), explainable matching, and safe transactional tagging with atomic rollbacks.

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
# Scan a directory recursively (multi-threaded) and report health summary, missing tags & duplicates
uv run patangoma scan ~/Music

# Output library statistics in machine-readable JSON
uv run patangoma scan ~/Music --json
```

### 2. File Inspection & Validation
```bash
# Inspect audio tags and technical audio properties (ReplayGain, sample rate, channels, bitrate)
uv run patangoma inspect song.mp3

# Pre-flight audio header check and corruption detector
uv run patangoma check-file song.mp3
```

### 3. Explainable Matching & Search
```bash
# Query metadata providers with explainable confidence scoring
uv run patangoma match song.mp3 --provider musicbrainz
uv run patangoma match song.mp3 --provider itunes
uv run patangoma match song.mp3 --provider discogs
uv run patangoma match song.mp3 --provider acoustid

# Query all providers simultaneously with conflict resolution
uv run patangoma match song.mp3 --provider multi
```

### 4. Safe Plan & Apply Workflow
```bash
# 1. Generate a deterministic change plan
uv run patangoma plan song.mp3 --provider itunes -o plan.json

# 2. Simulate changes in dry-run mode
uv run patangoma apply plan.json --dry-run

# 3. Apply changes with automatic backup
uv run patangoma apply plan.json
```

### 5. Structured Renamer & File Organizer
```bash
# Preview file renaming according to a pattern
uv run patangoma rename ~/Music --pattern "{track_number:02d} - {artist} - {title}.{file_format}" --dry-run

# Apply file renames
uv run patangoma rename ~/Music --pattern "{track_number:02d} - {artist} - {title}.{file_format}"
```

### 6. Duplicate Audio Detector
```bash
# Find duplicate audio files across bitrates and formats (FLAC/WAV lossless prioritized as keepers)
uv run patangoma duplicates ~/Music
```

### 7. Lyrics Retrieval & Embedding
```bash
# Fetch plain and synchronized LRC lyrics
uv run patangoma lyrics song.mp3

# Embed lyrics directly into audio file tags
uv run patangoma lyrics song.mp3 --embed
```

### 8. Instant Rollback & Audit History
```bash
# List past metadata mutations
uv run patangoma history

# Rollback the most recent operation
uv run patangoma rollback --latest

# Rollback all operations targeting a specific file or directory
uv run patangoma rollback --path ~/Music

# Export audit report to HTML or CSV
uv run patangoma export-audit audit_report.html --format html
```

### 9. Diagnostics & Verification
```bash
# Run system and provider environment diagnostics (checks fpcalc, backend, credentials)
uv run patangoma doctor
```

---

## 📚 Documentation

- [User Guide](docs/user_guide.md) — Comprehensive commands, batch processing, and workflows.
- [Troubleshooting](docs/troubleshooting.md) — Installation of `fpcalc` (Windows/Mac/Linux), credentials, and FAQs.
- [Metadata Providers](docs/providers.md) — Overview of all 7 supported providers, caching, and rate limits.
- [Architecture Guide](ARCHITECTURE.md) — Architectural layers, invariants, and design principles.
- [Development Guide](DEVELOPMENT.md) — Contributing, testing, and CI instructions.
