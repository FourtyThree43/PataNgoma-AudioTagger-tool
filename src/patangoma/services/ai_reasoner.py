"""Metadata heuristics and AI reasoning service for unstructured filenames and explainability."""

from __future__ import annotations

import contextlib
import re
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from patangoma.domain.models import MatchResult, TrackMetadata


class FilenameInference(BaseModel):
    """Extracted metadata hypothesis from an unstructured audio filename."""

    raw_stem: str
    suggested_title: str | None = None
    suggested_artist: str | None = None
    suggested_track_number: int | None = None
    confidence: str = "MEDIUM"


class MetadataReasoner:
    """Heuristic reasoning engine for unravelling noisy filenames and explaining matches."""

    # Common filename separators: "Artist - Title", "01. Artist - Title", "Title (feat. Artist)"
    _PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        # 01 - Artist - Title
        re.compile(
            r"^(?P<track>\d{1,3})[\s._-]+(?P<artist>[^\d-][^-]*)[\s._-]+(?P<title>.+)$"
        ),
        # 01 - Title or 01. Title
        re.compile(r"^(?P<track>\d{1,3})[\s._-]+(?P<title>.+)$"),
        # Artist - Title (artist cannot be purely numeric)
        re.compile(r"^(?P<artist>[^\d-][^-]*)[\s._-]+(?P<title>.+)$"),
        # Fallback Artist - Title
        re.compile(r"^(?P<artist>[^-]+)[\s._-]+(?P<title>.+)$"),
    ]

    _CLEANUP_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(r"\(official\s+video\)", re.IGNORECASE),
        re.compile(r"\(official\s+audio\)", re.IGNORECASE),
        re.compile(r"\[official\s+video\]", re.IGNORECASE),
        re.compile(r"\(lyrics?\s+video\)", re.IGNORECASE),
        re.compile(r"\(audio\)", re.IGNORECASE),
        re.compile(r"\[hq\]", re.IGNORECASE),
        re.compile(r"\[hd\]", re.IGNORECASE),
        re.compile(
            r"[\(\[\_\s-]*(320\s*kbps|128\s*kbps|256\s*kbps)[\)\]\s]*", re.IGNORECASE
        ),
    ]

    def parse_filename(self, filename: str) -> FilenameInference:
        """Infer title, artist, and track number from unstructured filename stem."""
        stem = Path(
            filename
        ).stem  # Extract filename stem without parent path or extension
        cleaned = stem

        # Strip quality/video junk tags
        for pat in self._CLEANUP_PATTERNS:
            cleaned = pat.sub(" ", cleaned)

        # Replace underscores with spaces and collapse whitespace
        cleaned = cleaned.replace("_", " ").strip()
        cleaned = re.sub(r"\s+", " ", cleaned)

        track_num: int | None = None
        artist: str | None = None
        title: str | None = None

        for pat in self._PATTERNS:
            m = pat.match(cleaned)
            if m:
                groups = m.groupdict()
                if groups.get("track"):
                    with contextlib.suppress(ValueError):
                        track_num = int(groups["track"])
                if groups.get("artist"):
                    artist = groups["artist"].strip()
                if groups.get("title"):
                    title = groups["title"].strip()
                break

        if not title:
            title = cleaned.strip()

        conf = "HIGH" if (artist and title) else ("MEDIUM" if title else "LOW")

        return FilenameInference(
            raw_stem=stem,
            suggested_title=title,
            suggested_artist=artist,
            suggested_track_number=track_num,
            confidence=conf,
        )

    def parse_with_custom_template(
        self, filename: str, template: str
    ) -> FilenameInference:
        """Parse filename using a user-specified template (e.g. '%track% - %artist% - %title%')."""
        stem = re.sub(r"\.[a-zA-Z0-9]+$", "", filename)
        pattern_str = re.escape(template)
        pattern_str = re.sub(r"\\?%track\\?%", r"(?P<track>\\d{1,3})", pattern_str)
        pattern_str = re.sub(r"\\?%artist\\?%", r"(?P<artist>.+?)", pattern_str)
        pattern_str = re.sub(r"\\?%album\\?%", r"(?P<album>.+?)", pattern_str)
        pattern_str = re.sub(r"\\?%title\\?%", r"(?P<title>.+?)", pattern_str)
        pattern_str = re.sub(r"\\?%year\\?%", r"(?P<year>\\d{4})", pattern_str)
        pattern_str = f"^{pattern_str}$"

        m = re.match(pattern_str, stem.strip())
        if not m:
            return self.parse_filename(filename)

        groups = m.groupdict()
        track_num = None
        if groups.get("track"):
            with contextlib.suppress(ValueError):
                track_num = int(groups["track"])

        return FilenameInference(
            raw_stem=stem,
            suggested_title=groups.get("title", "").strip() or None,
            suggested_artist=groups.get("artist", "").strip() or None,
            suggested_track_number=track_num,
            confidence="EXACT"
            if groups.get("title") and groups.get("artist")
            else "HIGH",
        )

    def explain_match(self, match: MatchResult) -> str:
        """Produce an explainable textual rationale for the candidate match score."""
        cand = match.candidate
        score = match.score
        conf = match.confidence

        reasons = list(score.breakdown_reasons)
        summary = (
            f"Candidate '{cand.title}' by '{cand.primary_artist}' "
            f"received a total confidence of {score.total_score * 100:.1f}% ({conf.value})."
        )
        if reasons:
            details = " Details: " + "; ".join(reasons) + "."
            return summary + details
        return summary

    def suggest_tag_improvements(self, track: TrackMetadata) -> list[str]:
        """Analyze track metadata and generate actionable improvement suggestions."""
        suggestions: list[str] = []

        if not track.title or not track.artist:
            inference = self.parse_filename(track.file_path)
            if inference.suggested_title and not track.title:
                suggestions.append(
                    f"Inferred title '{inference.suggested_title}' from filename."
                )
            if inference.suggested_artist and not track.artist:
                suggestions.append(
                    f"Inferred artist '{inference.suggested_artist}' from filename."
                )

        if not track.year:
            suggestions.append(
                "Missing release year — query MusicBrainz or Spotify to populate date tags."
            )

        if not track.has_artwork:
            suggestions.append(
                "Missing album artwork — fetch cover art via provider search."
            )

        if not track.album:
            suggestions.append(
                "Missing album name — evaluate matching releases to populate collection tags."
            )

        return suggestions
