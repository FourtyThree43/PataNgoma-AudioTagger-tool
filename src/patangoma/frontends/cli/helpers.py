"""CLI presentation helpers and candidate query routines."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import (
    MetadataCandidate,
    QueryParameters,
    TrackMetadata,
)
from patangoma.frontends.cli.state import console, reasoner
from patangoma.providers.registry import get_provider


def query_candidates(
    track: TrackMetadata, file_path: str, provider_name: str
) -> tuple[list[MetadataCandidate], str]:
    """Query metadata candidates with automatic filename heuristic fallback and multi-provider support."""
    q_title = track.title
    q_artist = track.artist
    q_album = track.album
    display_title = track.title or Path(file_path).name

    # Automatic fallback if title is missing from tags
    if not q_title:
        inf = reasoner.parse_filename(file_path)
        if inf.suggested_title:
            q_title = inf.suggested_title
            display_title = inf.suggested_title
            if not q_artist:
                q_artist = inf.suggested_artist
            console.print(
                f"[cyan]* Inferred title '[bold]{q_title}[/bold]'"
                + (f" by '{q_artist}'" if q_artist else "")
                + " from filename for lookup.[/cyan]"
            )

    norm_prov = provider_name.lower().strip()

    if norm_prov in ("multi", "all"):
        from patangoma.services.aggregator import MetadataAggregator

        agg = MetadataAggregator()
        cands = agg.search_all_providers(
            QueryParameters(
                title=q_title,
                artist=q_artist,
                album=q_album,
                isrc=track.isrc,
            )
        )
        return cands, display_title

    if norm_prov == "acoustid":
        from patangoma.plugins.metadata.acoustid import (
            find_fpcalc_binary,
            generate_chromaprint,
        )

        fpcalc_bin = find_fpcalc_binary()
        if fpcalc_bin:
            fp_info = generate_chromaprint(file_path)
            if fp_info:
                dur, fp = fp_info
                prov = get_provider("acoustid")
                return (
                    prov.lookup_fingerprint(dur, fp),
                    display_title,
                )

        console.print(
            "[yellow]⚠ fpcalc (Chromaprint) not found on system path. Using metadata text search...[/yellow]"
        )

    prov = get_provider(norm_prov)
    cands = prov.search_tracks(
        QueryParameters(
            title=q_title,
            artist=q_artist,
            album=q_album,
            isrc=track.isrc,
        )
    )
    return cands, display_title
