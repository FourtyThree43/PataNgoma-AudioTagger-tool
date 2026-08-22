"""Explainable metadata matching engine for PataNgoma."""

from __future__ import annotations

import difflib
import re
import unicodedata

from patangoma.domain.models import (
    ConfidenceLevel,
    MatchResult,
    MetadataCandidate,
    ScoreBreakdown,
    TrackMetadata,
)

# Standard noise patterns in track/album titles to strip during normalization
_NOISE_PATTERNS = [
    re.compile(r"\(official\s+video\)", re.IGNORECASE),
    re.compile(r"\(official\s+audio\)", re.IGNORECASE),
    re.compile(r"\(lyrics?\s+video\)", re.IGNORECASE),
    re.compile(r"\(remaster(ed)?(\s+\d{4})?\)", re.IGNORECASE),
    re.compile(r"\[remaster(ed)?(\s+\d{4})?\]", re.IGNORECASE),
    re.compile(r"\(bonus\s+track\)", re.IGNORECASE),
    re.compile(r"\(feat\.?.*?\)", re.IGNORECASE),
    re.compile(r"\[feat\.?.*?\]", re.IGNORECASE),
    re.compile(r"ft\.?\s+.*$", re.IGNORECASE),
]


def normalize_text(text: str | None) -> str:
    """Normalize text by lowercasing, stripping diacritics, and removing common music title artifacts."""
    if not text:
        return ""

    # Normalize unicode (NFD decomposes accents from letters)
    nfkd = unicodedata.normalize("NFKD", text)
    clean = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

    # Strip noise patterns
    for pattern in _NOISE_PATTERNS:
        clean = pattern.sub("", clean)

    # Replace punctuation with whitespace
    clean = re.sub(r"[^\w\s]", " ", clean)
    # Collapse multiple whitespace
    clean = re.sub(r"\s+", " ", clean).strip()

    return clean


def compute_string_similarity(a: str | None, b: str | None) -> float:
    """Compute normalized sequence similarity ratio between two strings (0.0 to 1.0)."""
    norm_a = normalize_text(a)
    norm_b = normalize_text(b)

    if not norm_a and not norm_b:
        return 1.0
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0

    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


def compute_artist_similarity(
    track_artist: str | None, candidate_artists: list[str]
) -> float:
    """Compute similarity between track artist and candidate artist list."""
    if not track_artist or not candidate_artists:
        return 0.0

    norm_track_artist = normalize_text(track_artist)

    # Check best single artist match
    best_score = 0.0
    for cand_art in candidate_artists:
        sim = compute_string_similarity(track_artist, cand_art)
        if sim > best_score:
            best_score = sim

    # Also check joined candidate artists
    joined_cand = normalize_text(", ".join(candidate_artists))
    joined_sim = difflib.SequenceMatcher(None, norm_track_artist, joined_cand).ratio()
    return max(best_score, joined_sim)


def compute_duration_score(
    track_dur: float | None, cand_dur: float | None
) -> tuple[float, str | None]:
    """Compute duration similarity score (0.0 - 1.0) and explanation."""
    if track_dur is None or cand_dur is None:
        return 0.5, "Duration not available (neutral weight)"

    diff = abs(track_dur - cand_dur)
    if diff <= 3.0:
        return 1.0, f"Duration match within {diff:.1f}s"
    elif diff <= 10.0:
        score = 1.0 - ((diff - 3.0) / 7.0) * 0.4  # drops from 1.0 to 0.6
        return score, f"Duration close (diff {diff:.1f}s)"
    elif diff <= 30.0:
        score = 0.6 - ((diff - 10.0) / 20.0) * 0.5  # drops from 0.6 to 0.1
        return max(0.0, score), f"Duration difference: {diff:.1f}s"
    else:
        return 0.0, f"Duration mismatch: {diff:.1f}s difference"


class MatchingEngine:
    """Computes explainable match scores between local track metadata and provider candidates."""

    WEIGHT_TITLE = 0.40
    WEIGHT_ARTIST = 0.35
    WEIGHT_ALBUM = 0.15
    WEIGHT_DURATION = 0.10

    def evaluate_match(
        self,
        track: TrackMetadata,
        candidate: MetadataCandidate,
    ) -> MatchResult:
        """Evaluate match score and confidence between track and candidate."""
        reasons: list[str] = []

        # 1. ISRC Check (Instant EXACT match if available and equal)
        if (
            track.isrc
            and candidate.isrc
            and track.isrc.strip().upper() == candidate.isrc.strip().upper()
        ):
            breakdown = ScoreBreakdown(
                title_score=1.0,
                artist_score=1.0,
                album_score=1.0,
                duration_score=1.0,
                total_score=1.0,
                reasons=[f"ISRC exact match: {track.isrc}"],
            )
            return MatchResult(
                track_path=track.file_path,
                candidate=candidate,
                score=breakdown,
                confidence=ConfidenceLevel.EXACT,
            )

        # 2. Title Score
        title_score = compute_string_similarity(track.title, candidate.title)
        reasons.append(
            f"Title similarity: {title_score * 100:.1f}% ('{track.title}' vs '{candidate.title}')"
        )

        # 3. Artist Score
        artist_score = compute_artist_similarity(track.artist, candidate.artists)
        reasons.append(
            f"Artist similarity: {artist_score * 100:.1f}% ('{track.artist}' vs '{', '.join(candidate.artists)}')"
        )

        # 4. Album Score
        if track.album and candidate.album:
            album_score = compute_string_similarity(track.album, candidate.album)
            reasons.append(
                f"Album similarity: {album_score * 100:.1f}% ('{track.album}' vs '{candidate.album}')"
            )
        else:
            album_score = 0.5  # neutral
            reasons.append("Album metadata omitted or missing (neutral weight)")

        # 5. Duration Score
        dur_score, dur_reason = compute_duration_score(
            track.duration_seconds, candidate.duration_seconds
        )
        if dur_reason:
            reasons.append(dur_reason)

        # Total weighted score
        total_score = (
            (title_score * self.WEIGHT_TITLE)
            + (artist_score * self.WEIGHT_ARTIST)
            + (album_score * self.WEIGHT_ALBUM)
            + (dur_score * self.WEIGHT_DURATION)
        )

        # Determine confidence level
        if total_score >= 0.93 and title_score >= 0.90 and artist_score >= 0.90:
            confidence = ConfidenceLevel.EXACT
        elif total_score >= 0.78 and title_score >= 0.70 and artist_score >= 0.70:
            confidence = ConfidenceLevel.HIGH
        elif total_score >= 0.60:
            confidence = ConfidenceLevel.MEDIUM
        elif total_score >= 0.40:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.NO_MATCH

        breakdown = ScoreBreakdown(
            title_score=title_score,
            artist_score=artist_score,
            album_score=album_score,
            duration_score=dur_score,
            total_score=round(total_score, 4),
            reasons=reasons,
        )

        return MatchResult(
            track_path=track.file_path,
            candidate=candidate,
            score=breakdown,
            confidence=confidence,
        )

    def rank_candidates(
        self,
        track: TrackMetadata,
        candidates: list[MetadataCandidate],
    ) -> list[MatchResult]:
        """Rank candidates in descending order of total score."""
        results = [self.evaluate_match(track, c) for c in candidates]
        results.sort(key=lambda r: r.score.total_score, reverse=True)
        return results
