# Metadata Providers & Integration Guide

PataNgoma features a multi-provider metadata aggregation engine. You can query individual providers directly or leverage the **Multi-Provider Aggregator** (`--provider multi`) to automatically merge, disambiguate, and rank candidates across all available sources.

---

## Supported Providers Overview

| Provider | Key Required? | Strengths | Supported Formats / Tags |
|---|---|---|---|
| **Apple iTunes** | ❌ No | Fast, high-resolution artwork (1400x1400), clean pop/mainstream catalogs | Title, Artist, Album, Year, Genre, Track#, Artwork |
| **MusicBrainz** | ❌ No | Authoritative release groups, multi-disc indices, acoustic MBIDs | Title, Artist, Album, Year, Date, Track#, Disc#, MBIDs |
| **Discogs** | ⚠️ Optional Token | Comprehensive physical vinyl, CD, cassette, and regional catalog data | Title, Artist, Album, Year, Genre, Country, Disc# |
| **Deezer** | ❌ No | Global streaming catalog, international releases, cover art | Title, Artist, Album, Year, Track#, Artwork |
| **Spotify** | 🔑 Client ID/Secret | Large streaming catalog, popularity rankings, ISRC matching | Title, Artist, Album, Year, ISRC, Artwork |
| **AcoustID** | 🔑 API Key + `fpcalc` | Audio fingerprinting matching via Chromaprint (`fpcalc`) | AcoustID Fingerprint, MBID Record matching |
| **LrcLib Lyrics** | ❌ No | Plain text and synchronized LRC timestamped lyrics | `lyrics`, `synced_lyrics` |

---

## 1. Multi-Provider Aggregator (`multi`)

The multi-provider aggregator simultaneously queries multiple upstream services, normalizes their payloads into uniform `MetadataCandidate` objects, removes duplicate candidates, and scores them using token-sort heuristics.

```bash
uv run patangoma match "song.mp3" --provider multi
uv run patangoma plan "song.mp3" --provider multi -o plan.json
```

---

## 2. Setting Up Credentials (`.env`)

For keyless providers (Apple iTunes, MusicBrainz, Deezer, LrcLib), no configuration is required out of the box.

For authenticated providers, set the environment variables in a `.env` file in the project root or your home directory:

```ini
# Spotify Developer API (Optional)
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret

# Discogs Personal Access Token (Optional)
DISCOGS_TOKEN=your_discogs_user_token

# AcoustID API Key (Optional)
ACOUSTID_API_KEY=your_acoustid_api_key

# MusicBrainz User-Agent Identification
MUSICBRAINZ_USER_AGENT=PataNgoma/1.5.0 (https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool)
```

---

## 3. Acoustic Fingerprinting (`fpcalc` / Chromaprint)

PataNgoma automatically searches standard system locations across platforms:
- **Linux**: `/usr/bin/fpcalc`, `/usr/local/bin/fpcalc` (Install: `sudo apt-get install libchromaprint-tools`)
- **macOS**: `/opt/homebrew/bin/fpcalc`, `/usr/local/bin/fpcalc` (Install: `brew install chromaprint`)
- **Windows**: `C:\Program Files\Chromaprint\fpcalc.exe` (Download from [AcoustID.org](https://acoustid.org/chromaprint))
