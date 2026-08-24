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
