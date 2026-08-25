# PataNgoma AudioTagger — Comprehensive User Guide

PataNgoma is a provider-agnostic audio metadata intelligence platform with explainable confidence scoring, multi-provider aggregation, and transactional rollback protection.

---

## 1. Quickstart & Verification

```bash
# Verify environment, audio backends, and fpcalc binary
uv run patangoma doctor

# Launch full continuous interactive TUI
uv run patangoma

# Launch interactive REPL session with slash commands
uv run patangoma session
```

---

## 2. Interactive TUI Mode (`uv run patangoma`)

Running `uv run patangoma` starts the continuous interactive terminal interface:
1. **Target Selection**: Select a track or folder using tab-completion.
2. **Action Menu**:
   - `🎯 Match & Tag Track`: Search across 7 providers or the multi-provider aggregator.
   - `👁️ Inspect Metadata`: View bitrate, sample rate, channels, and tags.
   - `✏️ Edit Tags`: Quick field form editor.
   - `📊 ReplayGain & Loudness`: Calculate EBU R128 loudness and peak tags.
   - `📂 Rename / Organize`: Organize tracks via custom metadata template patterns.
   - `📜 Synchronized Lyrics`: Download and embed synced `.lrc` lyrics.
   - `🧹 Normalize Genres`: Clean genres into a standardized 18-genre taxonomy.
   - `⏪ Rollback Changes`: Revert recent tag changes instantly via SQLite backups.
   - `📁 Choose Another File`: Switch active file or directory without leaving the TUI.
   - `🩺 Run Diagnostics`: Check audio codecs, providers, and database health.
   - `🚪 Exit`: Clean exit.

---

## 3. CLI Command Reference

### 3.1 Inspection & Validation
```bash
# Inspect audio properties and tags
uv run patangoma inspect "track.mp3"

# Check file integrity & magic headers
uv run patangoma check-file "track.mp3"

# Check audio transcoding quality (detect low-bitrate upsamples)
uv run patangoma transcode-check "track.flac"
```

### 3.2 Metadata Matching
```bash
# Query individual providers
uv run patangoma match "track.mp3" --provider itunes
uv run patangoma match "track.mp3" --provider musicbrainz
uv run patangoma match "track.mp3" --provider discogs
uv run patangoma match "track.mp3" --provider deezer
uv run patangoma match "track.mp3" --provider spotify

# Multi-Provider Aggregation (merge & rank all providers)
uv run patangoma match "track.mp3" --provider multi
```

### 3.3 Safe Tagging (Plan / Apply Workflow)
```bash
# Generate a mutation plan diff
uv run patangoma plan "track.mp3" --provider itunes -o plan.json

# Preview application in dry-run mode
uv run patangoma apply plan.json --dry-run

# Apply tags and record an atomic rollback snapshot
uv run patangoma apply plan.json --embed-artwork
```

### 3.4 Interactive Tagging
```bash
# Interactive candidate picker
uv run patangoma tag "track.mp3" --interactive

# Interactive field editor
uv run patangoma edit "track.mp3"
```

### 3.5 Batch Directory Operations
```bash
# Scan directory recursively
uv run patangoma scan /path/to/music/

# Generate plan for entire directory
uv run patangoma plan-dir /path/to/music/ --provider itunes -o batch_plan.json

# Apply batch plan with album art embedding
uv run patangoma apply-dir batch_plan.json --embed-artwork
```

### 3.6 ReplayGain Loudness Scanner
```bash
# Scan and apply peak & track gain tags
uv run patangoma replaygain /path/to/music/
```

### 3.7 Library Renaming & Multi-Disc Organization
```bash
# Rename single files or entire directories
uv run patangoma rename /path/to/music/ --pattern "{artist}/{album}/{track_number:02d} - {title}.{file_format}"

# Multi-disc pattern
uv run patangoma rename /path/to/music/ --pattern "{artist}/{album}/Disc {disc_number:02d}/{track_number:02d} - {title}.{file_format}"
```

### 3.8 Lyrics Retrieval
```bash
# View plain & synchronized lyrics
uv run patangoma lyrics "track.mp3"

# Embed lyrics into audio file
uv run patangoma lyrics "track.mp3" --embed
```

### 3.9 Genre Normalization
```bash
# Map messy tags ("hip hop/rap", "synth-wave") to canonical taxonomy
uv run patangoma normalize-genres /path/to/music/
```

### 3.10 Catalog & Playlist Exporter
```bash
# Export library catalog to JSON, CSV, or SQLite
uv run patangoma export-catalog /path/to/music/ --format sqlite -o catalog.db

# Export M3U8 playlist
uv run patangoma playlist-export /path/to/music/ -o playlist.m3u8

# Inspect .cue sheet
uv run patangoma cue-inspect "album.cue"
```

### 3.11 Rollback & Audit History
```bash
# View recent metadata changes
uv run patangoma history --limit 10

# Rollback last change
uv run patangoma rollback --latest

# Rollback specific operation ID
uv run patangoma rollback <operation_id>
```
