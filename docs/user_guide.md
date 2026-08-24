# PataNgoma AudioTagger — User Guide

PataNgoma is a provider-agnostic audio metadata intelligence platform with safe, explainable matching and transactional tagging.

---

## 1. Quickstart & Verification

```bash
# Verify environment and metadata backend
uv run patangoma doctor

# Generate a synthetic test library to experiment safely
uv run patangoma demo-library /tmp/music_demo

# Scan the test library
uv run patangoma scan /tmp/music_demo
```

---

## 2. Core Workflows

### 2.1 Inspection & Validation
Inspect metadata tags and technical audio properties (sample rate, channels, bitrate, ReplayGain):
```bash
uv run patangoma inspect "track.mp3"

# Validate audio header integrity and detect corrupt files
uv run patangoma check-file "track.mp3"
```

### 2.2 Explainable Matching
Search online providers and inspect confidence scoring breakdown:
```bash
# Match with MusicBrainz (default)
uv run patangoma match "track.mp3" --provider musicbrainz

# Match with keyless Apple iTunes API
uv run patangoma match "track.mp3" --provider itunes

# Match with Discogs
uv run patangoma match "track.mp3" --provider discogs

# Query all providers simultaneously
uv run patangoma match "track.mp3" --provider multi
```

### 2.3 Safe Mutation: Plan / Apply
Always preview before writing:
```bash
# Step 1: Generate plan
uv run patangoma plan "track.mp3" --provider itunes -o plan.json

# Step 2: Simulate in dry-run mode
uv run patangoma apply plan.json --dry-run

# Step 3: Apply changes with automatic rollback journal entry
uv run patangoma apply plan.json
```

### 2.4 Batch Directory Tagging
Tag an entire music folder deterministically:
```bash
# Step 1: Generate batch plan across entire directory
uv run patangoma plan-dir /path/to/music/ --provider itunes -o batch_plan.json

# Step 2: Apply batch plan
uv run patangoma apply-dir batch_plan.json
```

### 2.5 Library Renaming & Organization
Reorganize and rename files using structured metadata templates:
```bash
# Preview rename in dry-run mode
uv run patangoma rename /path/to/music/ --pattern "{track_number:02d} - {artist} - {title}.{file_format}" --dry-run

# Apply file renames
uv run patangoma rename /path/to/music/ --pattern "{track_number:02d} - {artist} - {title}.{file_format}"
```

### 2.6 Duplicate Audio Detection
Find duplicate tracks across formats and bitrates (lossless FLAC/WAV prioritized as keepers):
```bash
uv run patangoma duplicates /path/to/music/
```

### 2.7 Lyrics Retrieval
Fetch plain and synchronized LRC lyrics:
```bash
uv run patangoma lyrics "track.mp3"

# Embed lyrics directly into audio file tags
uv run patangoma lyrics "track.mp3" --embed
```

### 2.8 Rollback & Audit History
Revert changes at any time:
```bash
# View recent metadata mutations
uv run patangoma history

# Rollback the most recent operation
uv run patangoma rollback --latest

# Rollback all operations targeting a specific file or folder
uv run patangoma rollback --path /path/to/music/

# Export audit trail to HTML or CSV
uv run patangoma export-audit audit_report.html --format html
```
