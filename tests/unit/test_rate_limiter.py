"""Unit tests for ProviderRateLimiter."""

from __future__ import annotations

import time

from patangoma.providers.rate_limiter import ProviderRateLimiter, rate_limited


def test_rate_limiter_throttles():
    # 0.1 second interval
    limiter = ProviderRateLimiter(intervals={"test_prov": 0.05})

    t0 = time.time()
    w1 = limiter.acquire("test_prov")
    w2 = limiter.acquire("test_prov")
    t1 = time.time()

    assert w1 == 0.0
    assert w2 > 0.0
    assert (t1 - t0) >= 0.04


def test_rate_limited_decorator():
    limiter = ProviderRateLimiter(intervals={"mock": 0.05})

    class Client:
        name = "mock"

        @rate_limited(limiter=limiter)
        def call(self, x: int) -> int:
            return x * 2

    c = Client()
    t0 = time.time()
    c.call(1)
    c.call(2)
    t1 = time.time()

    assert (t1 - t0) >= 0.04
