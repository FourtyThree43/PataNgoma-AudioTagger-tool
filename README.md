# PataNgoma AudioTagger

[![CI](https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue)](https://www.python.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

**PataNgoma** is a provider-agnostic audio metadata intelligence platform built for deterministic music library scanning, multi-provider aggregation (MusicBrainz, Apple iTunes, Spotify, Deezer, Discogs, AcoustID, Lyrics), explainable matching, and safe transactional tagging with atomic rollbacks.

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

# Launch Continuous Interactive TUI
uv run patangoma

# Or launch Interactive REPL Session with slash commands
uv run patangoma session
```

---

## 🌐 Supported Metadata Providers

| Provider | Key Required? | Strengths |
|---|---|---|
| **Apple iTunes** | ❌ No | Fast, high-res artwork, reliable mainstream catalog |
| **MusicBrainz** | ❌ No | Authoritative release groups, multi-disc tracking, MBIDs |
| **Discogs** | ⚠️ Optional Token | Physical vinyl, CD, and regional release pressings |
| **Deezer** | ❌ No | Global catalog search and cover art |
| **Spotify** | 🔑 Client ID/Secret | Large streaming catalog and popularity ranking |
| **AcoustID** | 🔑 API Key + `fpcalc` | Audio fingerprint matching via Chromaprint |
| **LrcLib Lyrics** | ❌ No | Plain and synchronized LRC lyrics |

---

## 🛠️ Key CLI Workflows

### 1. File Inspection & Validation
```bash
# Inspect audio properties and tags
uv run patangoma inspect song.mp3

# Pre-flight audio header check and corruption detector
uv run patangoma check-file song.mp3

# Audio transcode quality check
uv run patangoma transcode-check song.flac
```

### 2. Explainable Matching & Search
```bash
# Search specific provider
uv run patangoma match song.mp3 --provider itunes

# Query all providers simultaneously with conflict resolution
uv run patangoma match song.mp3 --provider multi
```

### 3. Safe Plan & Apply Workflow
```bash
# 1. Generate a deterministic change plan
uv run patangoma plan song.mp3 --provider itunes -o plan.json

# 2. Simulate changes in dry-run mode
uv run patangoma apply plan.json --dry-run

# 3. Apply changes with automatic backup
uv run patangoma apply plan.json --embed-artwork
```

### 4. Interactive Tagging
```bash
# Interactive candidate picker
uv run patangoma tag song.mp3 --interactive

# Interactive field editor
uv run patangoma edit song.mp3
```

### 5. ReplayGain & Loudness Analysis
```bash
uv run patangoma replaygain ~/Music
```

### 6. Structured Renamer & File Organizer
```bash
uv run patangoma rename ~/Music --pattern "{track_number:02d} - {artist} - {title}.{file_format}"
```

### 7. Genre Normalization
```bash
uv run patangoma normalize-genres ~/Music
```

### 8. Catalog & Playlist Exporter
```bash
uv run patangoma export-catalog ~/Music --format sqlite -o catalog.db
uv run patangoma playlist-export ~/Music -o playlist.m3u8
uv run patangoma cue-inspect album.cue
```

### 9. Rollback & Audit History
```bash
uv run patangoma history --limit 10
uv run patangoma rollback --latest
```

---

## 🧪 Testing & Code Quality

```bash
# Run test suite with coverage
uv run pytest --cov=patangoma --cov-report=term-missing

# Lint & Format
uv run ruff check .
uv run ruff format --check .
```

---

## 📄 License

PataNgoma is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.
