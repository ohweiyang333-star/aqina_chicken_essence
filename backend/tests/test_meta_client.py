import requests
import pytest

from app.services.meta_client import MetaMessagingClient


def test_meta_http_error_includes_provider_body_without_access_token(monkeypatch):
    class FakeResponse:
        status_code = 400
        text = '{"error":{"message":"recipient is unavailable"}}'
        url = "https://graph.facebook.com/v22.0/me/messages?access_token=secret-token"

        def raise_for_status(self):
            raise requests.HTTPError(f"400 Client Error: Bad Request for url: {self.url}", response=self)

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse())

    with pytest.raises(requests.HTTPError) as error:
        MetaMessagingClient()._post(
            "/me/messages",
            params={"access_token": "secret-token"},
        )

    message = str(error.value)
    assert "recipient is unavailable" in message
    assert "secret-token" not in message
