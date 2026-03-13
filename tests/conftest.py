"""Shared fixtures for unit tests."""

from unittest.mock import AsyncMock

import pytest

from mcp_slack.api_models import (
    ChannelCreateResponse,
    ChannelHistoryResponse,
    ChannelListResponse,
    ChannelTopicResponse,
    PostMessageResponse,
    ReactionResponse,
    SearchMessagesResponse,
    ThreadRepliesResponse,
    UserInfoResponse,
)
from mcp_slack.server import mcp


@pytest.fixture
def mcp_server():
    """Return the MCP server instance."""
    return mcp


@pytest.fixture
def mock_client():
    """Create a mock API client with all methods stubbed."""
    client = AsyncMock()

    client.post_message = AsyncMock(
        return_value=PostMessageResponse(ok=True, channel="C123", ts="1234567890.123456")
    )
    client.list_channels = AsyncMock(
        return_value=ChannelListResponse(
            ok=True,
            channels=[
                {"id": "C123", "name": "general", "is_channel": True},
                {"id": "C456", "name": "random", "is_channel": True},
            ],
        )
    )
    client.create_channel = AsyncMock(
        return_value=ChannelCreateResponse(
            ok=True, channel={"id": "C789", "name": "new-channel", "is_channel": True}
        )
    )
    client.set_channel_topic = AsyncMock(
        return_value=ChannelTopicResponse(ok=True, topic="New topic")
    )
    client.get_channel_history = AsyncMock(
        return_value=ChannelHistoryResponse(
            ok=True,
            messages=[
                {"type": "message", "user": "U123", "text": "Hello", "ts": "1234567890.000001"},
                {"type": "message", "user": "U456", "text": "World", "ts": "1234567890.000002"},
            ],
            has_more=False,
        )
    )
    client.get_thread_replies = AsyncMock(
        return_value=ThreadRepliesResponse(
            ok=True,
            messages=[
                {"type": "message", "user": "U123", "text": "Parent", "ts": "1234567890.000001"},
                {"type": "message", "user": "U456", "text": "Reply", "ts": "1234567890.000003"},
            ],
            has_more=False,
        )
    )
    client.search_messages = AsyncMock(
        return_value=SearchMessagesResponse(
            ok=True,
            messages={
                "matches": [
                    {"text": "Found it", "ts": "1234567890.000001", "user": "U123"},
                ],
                "pagination": {"total_count": 1, "page": 1, "page_count": 1},
            },
        )
    )
    client.get_user_info = AsyncMock(
        return_value=UserInfoResponse(
            ok=True,
            user={"id": "U123", "name": "testuser", "real_name": "Test User"},
        )
    )
    client.add_reaction = AsyncMock(return_value=ReactionResponse(ok=True))

    return client
