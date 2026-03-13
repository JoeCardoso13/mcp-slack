"""Tests for Slack API models."""

from mcp_slack.api_models import (
    Channel,
    ChannelHistoryResponse,
    ChannelListResponse,
    Message,
    PostMessageResponse,
    ResponseMetadata,
    SearchMatch,
    SearchMessagesResponse,
    SlackResponse,
    User,
    UserInfoResponse,
    UserProfile,
)


def test_slack_response_ok() -> None:
    """Test base SlackResponse with ok=true."""
    resp = SlackResponse(ok=True)
    assert resp.ok is True
    assert resp.error is None


def test_slack_response_error() -> None:
    """Test base SlackResponse with error."""
    resp = SlackResponse(ok=False, error="channel_not_found")
    assert resp.ok is False
    assert resp.error == "channel_not_found"


def test_response_metadata() -> None:
    """Test cursor pagination metadata."""
    meta = ResponseMetadata(next_cursor="abc123")
    assert meta.next_cursor == "abc123"


def test_response_metadata_defaults() -> None:
    """Test ResponseMetadata defaults."""
    meta = ResponseMetadata()
    assert meta.next_cursor is None


def test_user_profile() -> None:
    """Test UserProfile model."""
    profile = UserProfile(
        real_name="Test User",
        display_name="testuser",
        email="test@example.com",
    )
    assert profile.real_name == "Test User"
    assert profile.email == "test@example.com"


def test_user_model() -> None:
    """Test User model."""
    user = User(
        id="U123",
        name="testuser",
        real_name="Test User",
        is_bot=False,
        is_admin=True,
    )
    assert user.id == "U123"
    assert user.is_admin is True
    assert user.deleted is False


def test_user_info_response() -> None:
    """Test UserInfoResponse parsing."""
    data = {
        "ok": True,
        "user": {
            "id": "U123",
            "name": "testuser",
            "real_name": "Test User",
            "profile": {"display_name": "Test"},
        },
    }
    resp = UserInfoResponse(**data)
    assert resp.ok is True
    assert resp.user is not None
    assert resp.user.id == "U123"
    assert resp.user.profile is not None


def test_channel_model() -> None:
    """Test Channel model."""
    channel = Channel(
        id="C123",
        name="general",
        is_channel=True,
        num_members=42,
    )
    assert channel.id == "C123"
    assert channel.name == "general"
    assert channel.is_private is False


def test_channel_list_response() -> None:
    """Test ChannelListResponse."""
    data = {
        "ok": True,
        "channels": [
            {"id": "C123", "name": "general"},
            {"id": "C456", "name": "random"},
        ],
        "response_metadata": {"next_cursor": "next_page"},
    }
    resp = ChannelListResponse(**data)
    assert len(resp.channels) == 2
    assert resp.response_metadata.next_cursor == "next_page"


def test_message_model() -> None:
    """Test Message model."""
    msg = Message(
        type="message",
        user="U123",
        text="Hello world",
        ts="1234567890.000001",
    )
    assert msg.text == "Hello world"
    assert msg.thread_ts is None


def test_post_message_response() -> None:
    """Test PostMessageResponse."""
    data = {
        "ok": True,
        "channel": "C123",
        "ts": "1234567890.000001",
        "message": {"text": "Hello"},
    }
    resp = PostMessageResponse(**data)
    assert resp.ok is True
    assert resp.ts == "1234567890.000001"


def test_channel_history_response() -> None:
    """Test ChannelHistoryResponse."""
    data = {
        "ok": True,
        "messages": [
            {"type": "message", "user": "U123", "text": "Hello", "ts": "1234.001"},
            {"type": "message", "user": "U456", "text": "World", "ts": "1234.002"},
        ],
        "has_more": True,
        "response_metadata": {"next_cursor": "page2"},
    }
    resp = ChannelHistoryResponse(**data)
    assert len(resp.messages) == 2
    assert resp.has_more is True


def test_search_match() -> None:
    """Test SearchMatch model."""
    match = SearchMatch(
        text="Found it",
        ts="1234.5678",
        user="U123",
        permalink="https://slack.com/archives/C123/p1234",
    )
    assert match.text == "Found it"
    assert match.permalink is not None


def test_search_messages_response() -> None:
    """Test SearchMessagesResponse."""
    data = {
        "ok": True,
        "messages": {
            "matches": [
                {"text": "result", "ts": "1234.001", "user": "U123"},
            ],
            "pagination": {"total_count": 1, "page": 1, "page_count": 1},
        },
    }
    resp = SearchMessagesResponse(**data)
    assert len(resp.messages.matches) == 1
    assert resp.messages.pagination.total_count == 1


def test_search_messages_empty() -> None:
    """Test SearchMessagesResponse with no results."""
    resp = SearchMessagesResponse(ok=True)
    assert resp.messages.matches == []
    assert resp.messages.pagination.total_count == 0
