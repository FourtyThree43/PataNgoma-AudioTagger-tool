"""Unit tests for AcoustID audio fingerprint provider."""

from __future__ import annotations

from unittest.mock import MagicMock

from patangoma.providers.acoustid import AcoustIDProvider


def test_acoustid_lookup_fingerprint():
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "ok",
        "results": [
            {
                "id": "result-123",
                "score": 0.95,
                "recordings": [
                    {
                        "id": "mb-recording-uuid-456",
                        "title": "Last Last",
                        "duration": 172,
                        "artists": [{"id": "mb-artist-uuid-789", "name": "Burna Boy"}],
                        "releases": [
                            {
                                "id": "mb-release-uuid-101",
                                "title": "Love, Damini",
                                "date": {"year": 2022},
                            }
                        ],
                    }
                ],
            }
        ],
    }
    mock_session.get.return_value = mock_resp

    provider = AcoustIDProvider(client_key="test_key", session=mock_session)
    candidates = provider.lookup_fingerprint(
        duration_seconds=172, fingerprint="AQADtHKUaUkSRd..."
    )

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.provider_name == "acoustid"
    assert cand.provider_id == "mb-recording-uuid-456"
    assert cand.title == "Last Last"
    assert cand.primary_artist == "Burna Boy"
    assert cand.album == "Love, Damini"
    assert cand.year == 2022
    assert cand.mb_trackid == "mb-recording-uuid-456"
    assert cand.mb_artistid == "mb-artist-uuid-789"


def test_find_fpcalc_binary(monkeypatch):
    from patangoma.providers.acoustid import find_fpcalc_binary

    monkeypatch.setenv("FPCALC_PATH", "/custom/bin/fpcalc")
    monkeypatch.setattr("pathlib.Path.is_file", lambda self: True)
    assert find_fpcalc_binary() == "/custom/bin/fpcalc"


def test_acoustid_search_tracks_text_fallback(monkeypatch):
    from patangoma.domain.models import MetadataCandidate, QueryParameters

    mock_cand = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="mb-123",
        title="LUMINOUS",
        artists=["Artist"],
    )
    mock_mb_instance = MagicMock()
    mock_mb_instance.search_tracks.return_value = [mock_cand]
    monkeypatch.setattr(
        "patangoma.providers.musicbrainz.MusicBrainzProvider",
        lambda *args, **kwargs: mock_mb_instance,
    )

    prov = AcoustIDProvider(use_cache=False)
    res = prov.search_tracks(QueryParameters(title="LUMINOUS"))
    assert len(res) == 1
    assert res[0].title == "LUMINOUS"
