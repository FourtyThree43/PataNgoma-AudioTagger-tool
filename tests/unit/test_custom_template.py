"""Unit tests for configurable filename template parsing in MetadataReasoner."""

from __future__ import annotations

from patangoma.services.ai_reasoner import MetadataReasoner


def test_parse_with_custom_template():
    reasoner = MetadataReasoner()

    # Template: %track% - %artist% - %title%
    inf1 = reasoner.parse_with_custom_template(
        "05 - Burna Boy - Last Last.mp3",
        template="%track% - %artist% - %title%",
    )
    assert inf1.suggested_track_number == 5
    assert inf1.suggested_artist == "Burna Boy"
    assert inf1.suggested_title == "Last Last"
    assert inf1.confidence == "EXACT"

    # Template: %artist% - %title% (%year%)
    inf2 = reasoner.parse_with_custom_template(
        "Sauti Sol - Suzanna (2020).flac",
        template="%artist% - %title% (%year%)",
    )
    assert inf2.suggested_artist == "Sauti Sol"
    assert inf2.suggested_title == "Suzanna"
