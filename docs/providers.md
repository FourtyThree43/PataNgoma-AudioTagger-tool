# PataNgoma Metadata Providers

PataNgoma features a multi-provider architecture with transparent two-tier caching (in-memory + SQLite) and per-provider rate limiting to prevent HTTP 429 throttling.

---

## Supported Providers

| Provider | Key Required? | Rate Limit | Highlights |
|---|---|---|---|
| **MusicBrainz** (`musicbrainz`) | ❌ No | 1.0 req/sec | Authoritative music database, MBIDs, ISRC, release date, release country. |
| **iTunes** (`itunes`) | ❌ No | 5.0 req/sec | High-res 600x600 artwork, instant lookups, release dates, track numbers. |
| **Deezer** (`deezer`) | ❌ No | 5.0 req/sec | Excellent pop/international coverage, preview URLs, release metadata. |
| **Spotify** (`spotify`) | Optional | 10.0 req/sec | Popularity metrics, album artwork, track audio features. |
| **Discogs** (`discogs`) | Optional | 1.0 req/sec | Deep vinyl catalog, physical release pressings, record label identifiers. |
| **AcoustID** (`acoustid`) | ❌ No | 3.0 req/sec | Acoustic waveform matching powered by Chromaprint fingerprints. |
| **Lyrics** (`lyrics`) | ❌ No | 5.0 req/sec | Plain and synchronized LRC timestamped lyrics powered by LrcLib. |

---

## Multi-Provider Aggregation

Use `--provider multi` or `--provider all` to query all registered providers concurrently:
```bash
uv run patangoma match "track.mp3" --provider multi
```
The aggregator executes parallel queries across providers, ranks candidates using token-sort string similarity and duration scoring, and merges unique metadata fields (e.g. MusicBrainz MBIDs + iTunes High-Res Artwork + Deezer Genres).
