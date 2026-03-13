"""Unit tests for the Slack API client."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from mcp_slack.api_client import SlackAPIError, SlackClient


@pytest_asyncio.fixture
async def mock_client():
    """Create a SlackClient with mocked session."""
    client = SlackClient(api_key="test_key")
    client._session = AsyncMock()
    yield client
    await client.close()


class TestClientInitialization:
    """Test client creation and configuration."""

    def test_init_with_explicit_key(self):
        """Client accepts an explicit API key."""
        client = SlackClient(api_key="xoxb-test")
        assert client.api_key == "xoxb-test"

    def test_init_with_env_var(self):
        """Client falls back to SLACK_API_KEY env var."""
        os.environ["SLACK_API_KEY"] = "xoxb-env"
        try:
            client = SlackClient()
            assert client.api_key == "xoxb-env"
        finally:
            del os.environ["SLACK_API_KEY"]

    def test_init_without_key_raises(self):
        """Client raises ValueError when no key is available."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SLACK_API_KEY", None)
            with pytest.raises(ValueError, match="SLACK_API_KEY is required"):
                SlackClient()

    def test_custom_timeout(self):
        """Client accepts a custom timeout."""
        client = SlackClient(api_key="key", timeout=60.0)
        assert client.timeout == 60.0

    def test_base_url(self):
        """Client uses the correct Slack API base URL."""
        assert SlackClient.BASE_URL == "https://slack.com/api"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Client works as an async context manager."""
        async with SlackClient(api_key="test") as client:
            assert client._session is not None
        assert client._session is None


class TestClientMethods:
    """Test API client methods with mocked responses."""

    @pytest.mark.asyncio
    async def test_post_message(self, mock_client):
        """Test posting a message."""
        mock_response = {"ok": True, "channel": "C123", "ts": "1234.5678"}
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.post_message(channel="C123", text="Hello")
        assert result.ok is True
        assert result.channel == "C123"

    @pytest.mark.asyncio
    async def test_list_channels(self, mock_client):
        """Test listing channels."""
        mock_response = {
            "ok": True,
            "channels": [{"id": "C123", "name": "general"}],
            "response_metadata": {"next_cursor": ""},
        }
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.list_channels()
        assert len(result.channels) == 1
        assert result.channels[0].id == "C123"

    @pytest.mark.asyncio
    async def test_get_user_info(self, mock_client):
        """Test getting user info."""
        mock_response = {
            "ok": True,
            "user": {"id": "U123", "name": "testuser", "real_name": "Test User"},
        }
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.get_user_info("U123")
        assert result.user is not None
        assert result.user.id == "U123"

    @pytest.mark.asyncio
    async def test_search_messages(self, mock_client):
        """Test searching messages."""
        mock_response = {
            "ok": True,
            "messages": {
                "matches": [{"text": "hello", "ts": "1234.5678"}],
                "pagination": {"total_count": 1, "page": 1, "page_count": 1},
            },
        }
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.search_messages(query="hello")
        assert len(result.messages.matches) == 1

    @pytest.mark.asyncio
    async def test_add_reaction(self, mock_client):
        """Test adding a reaction."""
        mock_response = {"ok": True}
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.add_reaction(
                channel="C123", timestamp="1234.5678", name="thumbsup"
            )
        assert result.ok is True


class TestErrorHandling:
    """Test error handling for API errors."""

    @pytest.mark.asyncio
    async def test_slack_error_response(self, mock_client):
        """Test handling of Slack ok=false errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=SlackAPIError(200, "channel_not_found"),
        ):
            with pytest.raises(SlackAPIError) as exc_info:
                await mock_client.post_message(channel="C999", text="fail")
            assert exc_info.value.message == "channel_not_found"

    @pytest.mark.asyncio
    async def test_401_unauthorized(self, mock_client):
        """Test handling of unauthorized errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=SlackAPIError(401, "invalid_auth"),
        ):
            with pytest.raises(SlackAPIError) as exc_info:
                await mock_client.list_channels()
            assert exc_info.value.status == 401

    @pytest.mark.asyncio
    async def test_429_rate_limit(self, mock_client):
        """Test handling of rate limit errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=SlackAPIError(429, "ratelimited"),
        ):
            with pytest.raises(SlackAPIError) as exc_info:
                await mock_client.search_messages(query="test")
            assert exc_info.value.status == 429

    @pytest.mark.asyncio
    async def test_network_error(self, mock_client):
        """Test handling of network errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=SlackAPIError(500, "Network error: Connection failed"),
        ):
            with pytest.raises(SlackAPIError) as exc_info:
                await mock_client.list_channels()
            assert exc_info.value.status == 500
            assert "Network error" in exc_info.value.message

    def test_error_string_representation(self):
        """Test error string format."""
        err = SlackAPIError(200, "channel_not_found", {"ok": False, "error": "channel_not_found"})
        assert "200" in str(err)
        assert "channel_not_found" in str(err)
        assert err.details is not None
