"""Tests for Slack MCP Server tools and skill resource."""

from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_slack.api_client import SlackAPIError
from mcp_slack.server import SKILL_CONTENT


class TestSkillResource:
    """Test the skill resource and server instructions."""

    @pytest.mark.asyncio
    async def test_initialize_returns_instructions(self, mcp_server):
        """Server instructions reference the skill resource."""
        async with Client(mcp_server) as client:
            result = await client.initialize()
            assert result.instructions is not None
            assert "skill://slack/usage" in result.instructions

    @pytest.mark.asyncio
    async def test_skill_resource_listed(self, mcp_server):
        """skill://slack/usage appears in resource listing."""
        async with Client(mcp_server) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert "skill://slack/usage" in uris

    @pytest.mark.asyncio
    async def test_skill_resource_readable(self, mcp_server):
        """Reading the skill resource returns the full skill content."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://slack/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert "send_message" in text

    @pytest.mark.asyncio
    async def test_skill_content_matches_constant(self, mcp_server):
        """Resource content matches the SKILL_CONTENT constant."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://slack/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert text == SKILL_CONTENT


class TestToolListing:
    """Test that all tools are registered and discoverable."""

    @pytest.mark.asyncio
    async def test_all_tools_listed(self, mcp_server):
        """All expected tools appear in tool listing."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools}
            expected = {
                "send_message",
                "reply_to_thread",
                "list_channels",
                "create_channel",
                "set_channel_topic",
                "get_channel_history",
                "get_thread_replies",
                "search_messages",
                "get_user_info",
                "add_reaction",
            }
            assert expected == names


class TestChatTools:
    """Test chat tools via FastMCP Client."""

    @pytest.mark.asyncio
    async def test_send_message(self, mcp_server, mock_client):
        """Test send_message tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "send_message", {"channel": "C123", "text": "Hello"}
                )
            assert result is not None
            mock_client.post_message.assert_called_once_with(channel="C123", text="Hello")

    @pytest.mark.asyncio
    async def test_reply_to_thread(self, mcp_server, mock_client):
        """Test reply_to_thread tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "reply_to_thread",
                    {"channel": "C123", "thread_ts": "1234.5678", "text": "Reply"},
                )
            assert result is not None
            mock_client.post_message.assert_called_once_with(
                channel="C123", text="Reply", thread_ts="1234.5678", reply_broadcast=False
            )

    @pytest.mark.asyncio
    async def test_send_message_api_error(self, mcp_server, mock_client):
        """Test send_message handles API errors."""
        mock_client.post_message.side_effect = SlackAPIError(200, "channel_not_found")
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                with pytest.raises(ToolError, match="channel_not_found"):
                    await client.call_tool("send_message", {"channel": "C999", "text": "fail"})


class TestChannelTools:
    """Test channel management tools."""

    @pytest.mark.asyncio
    async def test_list_channels(self, mcp_server, mock_client):
        """Test list_channels tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("list_channels", {})
            assert result is not None
            mock_client.list_channels.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_channel(self, mcp_server, mock_client):
        """Test create_channel tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("create_channel", {"name": "new-channel"})
            assert result is not None
            mock_client.create_channel.assert_called_once_with(name="new-channel", is_private=False)

    @pytest.mark.asyncio
    async def test_set_channel_topic(self, mcp_server, mock_client):
        """Test set_channel_topic tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "set_channel_topic", {"channel": "C123", "topic": "New topic"}
                )
            assert result is not None
            mock_client.set_channel_topic.assert_called_once_with(channel="C123", topic="New topic")


class TestHistoryTools:
    """Test history and thread tools."""

    @pytest.mark.asyncio
    async def test_get_channel_history(self, mcp_server, mock_client):
        """Test get_channel_history tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "get_channel_history", {"channel": "C123", "limit": 10}
                )
            assert result is not None
            mock_client.get_channel_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_thread_replies(self, mcp_server, mock_client):
        """Test get_thread_replies tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "get_thread_replies", {"channel": "C123", "thread_ts": "1234.5678"}
                )
            assert result is not None
            mock_client.get_thread_replies.assert_called_once()


class TestSearchTools:
    """Test search tools."""

    @pytest.mark.asyncio
    async def test_search_messages(self, mcp_server, mock_client):
        """Test search_messages tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("search_messages", {"query": "important"})
            assert result is not None
            mock_client.search_messages.assert_called_once()


class TestUserTools:
    """Test user tools."""

    @pytest.mark.asyncio
    async def test_get_user_info(self, mcp_server, mock_client):
        """Test get_user_info tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("get_user_info", {"user_id": "U123"})
            assert result is not None
            mock_client.get_user_info.assert_called_once_with(user="U123")


class TestReactionTools:
    """Test reaction tools."""

    @pytest.mark.asyncio
    async def test_add_reaction(self, mcp_server, mock_client):
        """Test add_reaction tool."""
        with patch("mcp_slack.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "add_reaction",
                    {"channel": "C123", "timestamp": "1234.5678", "emoji": "thumbsup"},
                )
            assert result is not None
            mock_client.add_reaction.assert_called_once_with(
                channel="C123", timestamp="1234.5678", name="thumbsup"
            )
