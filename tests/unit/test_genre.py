"""Unit tests for canonical genre taxonomy and normalization."""

from patangoma.services.genre import GenreNormalizer


def test_genre_normalizer_mappings() -> None:
    norm = GenreNormalizer()

    # Hip-hop variants
    assert norm.normalize("hip hop").canonical_genre == "Hip-Hop"
    assert norm.normalize("hip-hop").canonical_genre == "Hip-Hop"
    assert norm.normalize("rap").canonical_genre == "Hip-Hop"
    assert norm.normalize("hip hop/rap").canonical_genre == "Hip-Hop"

    # Electronic variants
    assert norm.normalize("synth pop").canonical_genre == "Synthpop"
    assert norm.normalize("dnb").canonical_genre == "Drum & Bass"

    # R&B variants
    assert norm.normalize("rnb").canonical_genre == "R&B"
    assert norm.normalize("r and b").canonical_genre == "R&B"

    # Title-case fallback
    assert (
        norm.normalize("progressive metalcore").canonical_genre
        == "Progressive Metalcore"
    )

    # Empty
    assert norm.normalize("").canonical_genre == ""


def test_genre_normalizer_custom_overrides() -> None:
    norm = GenreNormalizer(custom_overrides={"my custom style": "Custom Style"})
    res = norm.normalize("my custom style")
    assert res.canonical_genre == "Custom Style"
    assert res.changed is True
