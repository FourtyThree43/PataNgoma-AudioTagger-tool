# PataNgoma AudioTagger — Troubleshooting Guide

This guide covers common issues and resolution steps across Linux, macOS, and Windows.

---

## 1. Acoustic Fingerprinting & `fpcalc`

### Symptom
When matching with `--provider acoustid`, the CLI displays:
```text
⚠ fpcalc (Chromaprint binary) not found on system path. Using metadata text search...
```

### Resolution
Install the Chromaprint CLI tool (`fpcalc`) for your operating system:

- **Windows (Scoop)**:
  ```bash
  scoop install chromaprint
  ```
- **Windows (Chocolatey)**:
  ```powershell
  choco install chromaprint
  ```
- **macOS (Homebrew)**:
  ```bash
  brew install chromaprint
  ```
- **Linux (Debian/Ubuntu)**:
  ```bash
  sudo apt install libchromaprint-tools
  ```
- **Linux (Fedora/RHEL)**:
  ```bash
  sudo dnf install chromaprint-tools
  ```
- **Linux (Arch)**:
  ```bash
  sudo pacman -S chromaprint
  ```

Alternatively, set the custom environment variable pointing directly to your binary:
```bash
export FPCALC_PATH=/path/to/fpcalc
```

---

## 2. Untagged Audio Files (Missing Title / Artist Tags)

### Behavior
When an audio file contains no embedded ID3/Vorbis tags (e.g. `09 - LUMINOUS.mp3`):
- PataNgoma's `MetadataReasoner` automatically extracts the title, track number, and artist from the filename pattern.
- Search queries use this inferred title and search across online providers seamlessly.

---

## 3. Spotify API Credentials (Optional)

### Symptom
`patangoma doctor` shows:
```text
Spotify Credentials: ⚠ WARNING (Spotify API credentials not set)
```

### Resolution
Spotify requires OAuth client credentials for API access. Create a free developer application at [developer.spotify.com](https://developer.spotify.com) and add the keys to your `.env` file:
```env
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
```
*(Note: MusicBrainz, iTunes, Deezer, and LrcLib do not require any API keys.)*

---

## 4. Discogs API Token (Optional)

### Resolution
For extended Discogs rate limits, generate a personal access token under your Discogs Account Settings -> Developers, and add it to `.env`:
```env
DISCOGS_TOKEN=your_discogs_token_here
```

---

## 5. Corrupt or Unreadable Audio Files

### Symptom
`patangoma scan` flags files under `Corrupt / Unreadable`.

### Resolution
Run pre-flight integrity verification on the specific file:
```bash
uv run patangoma check-file "/path/to/corrupt.mp3"
```
The validator checks magic bytes (`ID3`, `fLaC`, `RIFF`, `OggS`, `ftyp`) to determine whether the header is corrupted or unreadable.
