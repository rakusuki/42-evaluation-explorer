from __future__ import annotations

from app.forty_two import FortyTwoClient


def test_retry_after_is_bounded() -> None:
    client = FortyTwoClient()
    assert client._parse_retry_after(None) == 1
    assert client._parse_retry_after("0") == 1
    assert client._parse_retry_after("2") == 2
    assert client._parse_retry_after("999") <= client.config.max_retry_after_seconds
    assert client._parse_retry_after("not-a-number") == 1
