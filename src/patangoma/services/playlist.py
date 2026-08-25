"""M3U8 playlist generator and Cue sheet parser service."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from patangoma.services.audio_backend import AudioBackend


class CueTrack(BaseModel):
    """A track entry extracted from a Cue sheet."""

    track_number: int
    title: str
    artist: str | None = None
    index_time: str | None = None


class PlaylistService:
    """Exports structured M3U/M3U8 playlists and parses Cue sheets."""

    def __init__(self, backend: AudioBackend | None = None) -> None:
        self.backend = backend or AudioBackend()

    def export_m3u8(
        self,
        file_paths: list[str | Path],
        output_playlist: str | Path,
        relative_paths: bool = True,
        extended_info: bool = True,
    ) -> Path:
        """Write an extended UTF-8 M3U8 playlist."""
        out_path = Path(output_playlist)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines: list[str] = ["#EXTM3U"]

        for fp in file_paths:
            path_obj = Path(fp)
            if not path_obj.exists():
                continue

            if extended_info:
                try:
                    meta = self.backend.read_metadata(str(path_obj))
                    dur = int(meta.duration_seconds or -1)
                    artist = meta.artist or "Unknown Artist"
                    title = meta.title or path_obj.stem
                    lines.append(f"#EXTINF:{dur},{artist} - {title}")
                except Exception:
                    lines.append(f"#EXTINF:-1,{path_obj.stem}")

            if relative_paths:
                try:
                    rel_p = os.path.relpath(path_obj, out_path.parent)
                    lines.append(rel_p)
                except ValueError:
                    lines.append(str(path_obj.resolve()))
            else:
                lines.append(str(path_obj.resolve()))

        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path

    def parse_cue_sheet(self, cue_path: str | Path) -> list[CueTrack]:
        """Parse a .cue sheet file and extract track metadata."""
        cue_file = Path(cue_path)
        if not cue_file.exists():
            return []

        content = cue_file.read_text(encoding="utf-8", errors="replace")
        tracks: list[CueTrack] = []

        current_track: dict[str, Any] = {}
        album_performer = None

        for line in content.splitlines():
            line = line.strip()
            if line.startswith("PERFORMER") and not current_track:
                m = re.match(r'PERFORMER\s+"?([^"]+)"?', line, re.IGNORECASE)
                if m:
                    album_performer = m.group(1)

            elif line.startswith("TRACK"):
                if current_track and "number" in current_track:
                    tracks.append(
                        CueTrack(
                            track_number=current_track["number"],
                            title=current_track.get(
                                "title", f"Track {current_track['number']}"
                            ),
                            artist=current_track.get("artist", album_performer),
                            index_time=current_track.get("index_time"),
                        )
                    )
                m = re.match(r"TRACK\s+(\d+)\s+AUDIO", line, re.IGNORECASE)
                num = int(m.group(1)) if m else len(tracks) + 1
                current_track = {"number": num, "artist": album_performer}

            elif line.startswith("TITLE") and current_track:
                m = re.match(r'TITLE\s+"?([^"]+)"?', line, re.IGNORECASE)
                if m:
                    current_track["title"] = m.group(1)

            elif line.startswith("PERFORMER") and current_track:
                m = re.match(r'PERFORMER\s+"?([^"]+)"?', line, re.IGNORECASE)
                if m:
                    current_track["artist"] = m.group(1)

            elif line.startswith("INDEX 01") and current_track:
                parts = line.split()
                if len(parts) >= 3:
                    current_track["index_time"] = parts[2]

        if current_track and "number" in current_track:
            tracks.append(
                CueTrack(
                    track_number=current_track["number"],
                    title=current_track.get(
                        "title", f"Track {current_track['number']}"
                    ),
                    artist=current_track.get("artist", album_performer),
                    index_time=current_track.get("index_time"),
                )
            )

        return tracks
