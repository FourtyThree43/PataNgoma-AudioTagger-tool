# Troubleshooting & Diagnostics Guide

This document provides resolutions for common issues encountered during library scanning, provider querying, and file tagging.

---

## 1. Run Environment Diagnostics First

Always start by running:
```bash
uv run patangoma doctor
```
The diagnostics check will verify:
- Python runtime compatibility (`>=3.10`)
- Tagging audio backends (`Mutagen` / `MediaFile`)
- Registered providers and credentials
- Audit database access (`platformdirs` user data directory)
- `fpcalc` binary discovery for acoustic fingerprinting

---

## 2. Common Issues & Solutions

### A. `fpcalc` Not Found
**Symptom**: Acoustic fingerprinting fails with `fpcalc binary not found on PATH`.
**Solution**:
- **Linux**: `sudo apt-get install libchromaprint-tools` or `sudo dnf install chromaprint-tools`
- **macOS**: `brew install chromaprint`
- **Windows**: Download `fpcalc.exe` from [AcoustID.org](https://acoustid.org/chromaprint) and place in `C:\Program Files\Chromaprint\` or your system `PATH`.

### B. No Metadata Candidates Found for Untagged Track
**Symptom**: Audio files without existing title/artist tags return no candidates on search.
**Solution**:
- PataNgoma automatically uses filename heuristics (e.g. `09 - LUMINOUS.mp3` -> title: `LUMINOUS`, track: `9`).
- If filename is obscure (e.g., `track_01.mp3`), use `--interactive` or `/tag` to provide a manual title search query, or use `--provider multi` for acoustic fingerprinting.

### C. Rate Limits or Provider Timeouts
**Symptom**: `ProviderUnavailableError` or slow queries.
**Solution**:
- PataNgoma features automatic token-bucket rate limiting and an SQLite cache.
- For high-volume tagging, use the keyless **Apple iTunes provider** (`--provider itunes`), which has generous rate limits and low latency.

### D. File Read-Only or Permission Denied
**Symptom**: `TagWriteError: [Errno 13] Permission denied`.
**Solution**:
- Ensure you have write permissions to the audio file and its parent folder.
- On Windows/WSL, verify files are not locked by an active music player daemon.

---

## 3. Reverting Unwanted Changes (Rollback)

If a tag write or file rename produced unexpected results, revert using the transactional rollback journal:
```bash
# View last 10 mutation records
uv run patangoma history --limit 10

# Revert the most recent operation
uv run patangoma rollback --latest

# Revert a specific operation by UUID
uv run patangoma rollback <operation_id>
```
