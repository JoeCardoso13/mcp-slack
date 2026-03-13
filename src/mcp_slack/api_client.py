"""Async HTTP client for the Slack Web API."""

import os
from typing import Any

import aiohttp
from aiohttp import ClientError

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


class SlackAPIError(Exception):
    """Exception raised for Slack API errors."""

    def __init__(self, status: int, message: str, details: dict[str, Any] | None = None) -> None:
        self.status = status
        self.message = message
        self.details = details
        super().__init__(f"Slack API Error {status}: {message}")


class SlackClient:
    """Async client for the Slack Web API."""

    BASE_URL = "https://slack.com/api"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("SLACK_API_KEY")
        if not self.api_key:
            raise ValueError("SLACK_API_KEY is required")
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "SlackClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _ensure_session(self) -> None:
        if not self._session:
            headers = {
                "User-Agent": "mcp-server-slack/0.1.0",
                "Authorization": f"Bearer {self.api_key}",
            }
            self._session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Slack API.

        Slack returns HTTP 200 for most errors; the actual error is in the JSON body.
        """
        await self._ensure_session()
        url = f"{self.BASE_URL}{path}"

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            if not self._session:
                raise RuntimeError("Session not initialized")

            kwargs: dict[str, Any] = {}
            if json_data is not None:
                kwargs["json"] = json_data
            if params:
                kwargs["params"] = params

            async with self._session.request(method, url, **kwargs) as response:
                result = await response.json()

                # Slack returns HTTP 200 even for errors; check "ok" field
                if response.status >= 400:
                    error_msg = result.get("error", f"HTTP {response.status}")
                    raise SlackAPIError(response.status, error_msg, result)

                if isinstance(result, dict) and not result.get("ok", True):
                    error_msg = result.get("error", "Unknown error")
                    raise SlackAPIError(200, error_msg, result)

                return result

        except ClientError as e:
            raise SlackAPIError(500, f"Network error: {str(e)}") from e

    # ========================================================================
    # Chat Methods
    # ========================================================================

    async def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
        reply_broadcast: bool = False,
    ) -> PostMessageResponse:
        """Post a message to a channel or DM."""
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if reply_broadcast:
            payload["reply_broadcast"] = True
        data = await self._request("POST", "/chat.postMessage", json_data=payload)
        return PostMessageResponse(**data)

    # ========================================================================
    # Conversation Methods
    # ========================================================================

    async def list_channels(
        self,
        types: str = "public_channel",
        exclude_archived: bool = True,
        limit: int = 100,
        cursor: str | None = None,
    ) -> ChannelListResponse:
        """List channels in the workspace."""
        params: dict[str, Any] = {
            "types": types,
            "exclude_archived": str(exclude_archived).lower(),
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        data = await self._request("GET", "/conversations.list", params=params)
        return ChannelListResponse(**data)

    async def create_channel(
        self,
        name: str,
        is_private: bool = False,
    ) -> ChannelCreateResponse:
        """Create a new channel."""
        payload: dict[str, Any] = {"name": name, "is_private": is_private}
        data = await self._request("POST", "/conversations.create", json_data=payload)
        return ChannelCreateResponse(**data)

    async def set_channel_topic(
        self,
        channel: str,
        topic: str,
    ) -> ChannelTopicResponse:
        """Set a channel's topic."""
        payload = {"channel": channel, "topic": topic}
        data = await self._request("POST", "/conversations.setTopic", json_data=payload)
        return ChannelTopicResponse(**data)

    async def get_channel_history(
        self,
        channel: str,
        limit: int = 20,
        cursor: str | None = None,
        oldest: str | None = None,
        latest: str | None = None,
    ) -> ChannelHistoryResponse:
        """Get recent messages from a channel."""
        params: dict[str, Any] = {"channel": channel, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest
        data = await self._request("GET", "/conversations.history", params=params)
        return ChannelHistoryResponse(**data)

    async def get_thread_replies(
        self,
        channel: str,
        ts: str,
        limit: int = 100,
        cursor: str | None = None,
    ) -> ThreadRepliesResponse:
        """Get replies in a thread."""
        params: dict[str, Any] = {"channel": channel, "ts": ts, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = await self._request("GET", "/conversations.replies", params=params)
        return ThreadRepliesResponse(**data)

    # ========================================================================
    # Search Methods
    # ========================================================================

    async def search_messages(
        self,
        query: str,
        count: int = 20,
        sort: str = "timestamp",
        sort_dir: str = "desc",
        cursor: str | None = None,
    ) -> SearchMessagesResponse:
        """Search messages across the workspace."""
        params: dict[str, Any] = {
            "query": query,
            "count": count,
            "sort": sort,
            "sort_dir": sort_dir,
        }
        if cursor:
            params["cursor"] = cursor
        data = await self._request("GET", "/search.messages", params=params)
        return SearchMessagesResponse(**data)

    # ========================================================================
    # User Methods
    # ========================================================================

    async def get_user_info(self, user: str) -> UserInfoResponse:
        """Get user profile information."""
        data = await self._request("GET", "/users.info", params={"user": user})
        return UserInfoResponse(**data)

    # ========================================================================
    # Reaction Methods
    # ========================================================================

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str,
    ) -> ReactionResponse:
        """Add an emoji reaction to a message."""
        payload = {"channel": channel, "timestamp": timestamp, "name": name}
        data = await self._request("POST", "/reactions.add", json_data=payload)
        return ReactionResponse(**data)
