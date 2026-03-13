"""Pydantic models for Slack API responses."""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Common Models
# ============================================================================


class SlackResponse(BaseModel):
    """Base Slack API response — all endpoints return ok + optional error."""

    ok: bool = Field(..., description="Whether the API call succeeded")
    error: str | None = Field(None, description="Error code if ok is false")


class ResponseMetadata(BaseModel):
    """Cursor-based pagination metadata."""

    model_config = {"populate_by_name": True}

    next_cursor: str | None = Field(
        default=None, alias="next_cursor", description="Next page cursor"
    )


# ============================================================================
# User Models
# ============================================================================


class UserProfile(BaseModel):
    """Slack user profile."""

    model_config = {"populate_by_name": True}

    real_name: str | None = Field(None, description="User's full name")
    display_name: str | None = Field(None, description="User's display name")
    email: str | None = Field(None, description="User's email")
    status_text: str | None = Field(None, description="Custom status text")
    status_emoji: str | None = Field(None, description="Custom status emoji")
    image_72: str | None = Field(None, description="72px avatar URL")


class User(BaseModel):
    """Slack user."""

    id: str = Field(..., description="User ID")
    name: str | None = Field(None, description="Username")
    real_name: str | None = Field(None, description="Full name")
    deleted: bool = Field(default=False, description="Whether user is deactivated")
    is_bot: bool = Field(default=False, description="Whether user is a bot")
    is_admin: bool = Field(default=False, description="Whether user is a workspace admin")
    tz: str | None = Field(None, description="Timezone identifier")
    profile: UserProfile | None = Field(None, description="User profile")


class UserInfoResponse(SlackResponse):
    """Response for users.info."""

    user: User | None = Field(None, description="User object")


# ============================================================================
# Channel Models
# ============================================================================


class Topic(BaseModel):
    """Channel topic or purpose."""

    value: str = Field(default="", description="Topic text")


class Channel(BaseModel):
    """Slack channel/conversation."""

    id: str = Field(..., description="Channel ID")
    name: str | None = Field(None, description="Channel name")
    is_channel: bool = Field(default=False, description="Is a public channel")
    is_private: bool = Field(default=False, description="Is a private channel")
    is_archived: bool = Field(default=False, description="Is archived")
    is_member: bool = Field(default=False, description="Bot/user is a member")
    num_members: int | None = Field(None, description="Number of members")
    topic: Topic | None = Field(None, description="Channel topic")
    purpose: Topic | None = Field(None, description="Channel purpose")


class ChannelListResponse(SlackResponse):
    """Response for conversations.list."""

    channels: list[Channel] = Field(default_factory=list)
    response_metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class ChannelCreateResponse(SlackResponse):
    """Response for conversations.create."""

    channel: Channel | None = Field(None)


class ChannelTopicResponse(SlackResponse):
    """Response for conversations.setTopic."""

    topic: str | None = Field(None)


# ============================================================================
# Message Models
# ============================================================================


class Message(BaseModel):
    """Slack message."""

    type: str | None = Field(None, description="Message type")
    user: str | None = Field(None, description="User ID who sent the message")
    text: str | None = Field(None, description="Message text")
    ts: str | None = Field(None, description="Message timestamp (unique ID)")
    thread_ts: str | None = Field(None, description="Parent thread timestamp")
    reply_count: int | None = Field(None, description="Number of replies")


class PostMessageResponse(SlackResponse):
    """Response for chat.postMessage."""

    channel: str | None = Field(None, description="Channel ID")
    ts: str | None = Field(None, description="Message timestamp")
    message: dict[str, Any] | None = Field(None, description="Posted message object")


class ChannelHistoryResponse(SlackResponse):
    """Response for conversations.history."""

    messages: list[Message] = Field(default_factory=list)
    has_more: bool = Field(default=False)
    response_metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class ThreadRepliesResponse(SlackResponse):
    """Response for conversations.replies."""

    messages: list[Message] = Field(default_factory=list)
    has_more: bool = Field(default=False)
    response_metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


# ============================================================================
# Search Models
# ============================================================================


class SearchMatch(BaseModel):
    """A single search result match."""

    channel: dict[str, Any] | None = Field(None, description="Channel info")
    text: str | None = Field(None, description="Message text")
    ts: str | None = Field(None, description="Message timestamp")
    user: str | None = Field(None, description="User ID")
    permalink: str | None = Field(None, description="Permalink to message")


class SearchPagination(BaseModel):
    """Search pagination info."""

    total_count: int = Field(default=0)
    page: int = Field(default=1)
    page_count: int = Field(default=0)


class SearchMessages(BaseModel):
    """Search messages result container."""

    matches: list[SearchMatch] = Field(default_factory=list)
    pagination: SearchPagination = Field(default_factory=SearchPagination)


class SearchMessagesResponse(SlackResponse):
    """Response for search.messages."""

    messages: SearchMessages = Field(default_factory=SearchMessages)


# ============================================================================
# Reaction Models
# ============================================================================


class ReactionResponse(SlackResponse):
    """Response for reactions.add."""

    pass
