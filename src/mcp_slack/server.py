"""Slack MCP Server - FastMCP Implementation.

Provides tools for interacting with the Slack Web API:
messaging, channel management, search, user info, and reactions.
"""

import logging
import os
import sys
from importlib.resources import files

from fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_slack.api_client import SlackAPIError, SlackClient

# Logging setup - all logs to stderr (stdout is reserved for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_slack")

logger.info("Slack server module loading...")

SKILL_CONTENT = files("mcp_slack").joinpath("SKILL.md").read_text()

# Create MCP server
mcp = FastMCP(
    "Slack",
    instructions=(
        "Before using tools, read the skill://slack/usage resource "
        "for tool selection guidance and workflow patterns."
    ),
)

# Global client instance (lazy initialization)
_client: SlackClient | None = None


def get_client(ctx: Context | None = None) -> SlackClient:
    """Get or create the API client instance."""
    global _client
    if _client is None:
        api_key = os.environ.get("SLACK_API_KEY")
        if not api_key:
            msg = "SLACK_API_KEY environment variable is required"
            raise ValueError(msg)
        _client = SlackClient(api_key=api_key)
    return _client


# Health endpoint for HTTP transport
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "healthy", "service": "mcp-slack"})


# ============================================================================
# Chat Tools
# ============================================================================


@mcp.tool()
async def send_message(
    channel: str,
    text: str,
    ctx: Context | None = None,
) -> dict:
    """Send a message to a Slack channel or DM.

    Args:
        channel: Channel ID (e.g. C1234567890) or channel name (e.g. #general)
        text: Message text to send (supports Slack markdown/mrkdwn)
        ctx: MCP context for logging

    Returns:
        Posted message details including channel and timestamp
    """
    client = get_client(ctx)
    try:
        result = await client.post_message(channel=channel, text=text)
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def reply_to_thread(
    channel: str,
    thread_ts: str,
    text: str,
    broadcast: bool = False,
    ctx: Context | None = None,
) -> dict:
    """Reply to a specific message thread in Slack.

    Args:
        channel: Channel ID containing the thread
        thread_ts: Timestamp of the parent message to reply to
        text: Reply text (supports Slack markdown/mrkdwn)
        broadcast: If true, also post the reply to the channel
        ctx: MCP context for logging

    Returns:
        Posted reply details including channel and timestamp
    """
    client = get_client(ctx)
    try:
        result = await client.post_message(
            channel=channel, text=text, thread_ts=thread_ts, reply_broadcast=broadcast
        )
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Channel Tools
# ============================================================================


@mcp.tool()
async def list_channels(
    types: str = "public_channel",
    exclude_archived: bool = True,
    limit: int = 100,
    cursor: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """List channels in the Slack workspace.

    Args:
        types: Comma-separated channel types: public_channel, private_channel, mpim, im
        exclude_archived: Whether to exclude archived channels (default true)
        limit: Maximum channels to return, 1-1000 (default 100)
        cursor: Pagination cursor from a previous response
        ctx: MCP context for logging

    Returns:
        List of channels with pagination metadata
    """
    client = get_client(ctx)
    try:
        result = await client.list_channels(
            types=types, exclude_archived=exclude_archived, limit=limit, cursor=cursor
        )
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def create_channel(
    name: str,
    is_private: bool = False,
    ctx: Context | None = None,
) -> dict:
    """Create a new Slack channel.

    Args:
        name: Channel name (lowercase, numbers, hyphens, underscores; max 80 chars)
        is_private: Create as a private channel (default false)
        ctx: MCP context for logging

    Returns:
        Created channel details
    """
    client = get_client(ctx)
    try:
        result = await client.create_channel(name=name, is_private=is_private)
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def set_channel_topic(
    channel: str,
    topic: str,
    ctx: Context | None = None,
) -> dict:
    """Set the topic of a Slack channel.

    Args:
        channel: Channel ID to update
        topic: New topic text (max 250 characters)
        ctx: MCP context for logging

    Returns:
        Updated topic details
    """
    client = get_client(ctx)
    try:
        result = await client.set_channel_topic(channel=channel, topic=topic)
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# History & Thread Tools
# ============================================================================


@mcp.tool()
async def get_channel_history(
    channel: str,
    limit: int = 20,
    cursor: str | None = None,
    oldest: str | None = None,
    latest: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Read recent messages from a Slack channel.

    Args:
        channel: Channel ID to fetch history from
        limit: Maximum messages to return, 1-999 (default 20)
        cursor: Pagination cursor from a previous response
        oldest: Only messages after this Unix timestamp
        latest: Only messages before this Unix timestamp
        ctx: MCP context for logging

    Returns:
        List of messages with pagination metadata
    """
    client = get_client(ctx)
    try:
        result = await client.get_channel_history(
            channel=channel, limit=limit, cursor=cursor, oldest=oldest, latest=latest
        )
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def get_thread_replies(
    channel: str,
    thread_ts: str,
    limit: int = 100,
    cursor: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Read all replies in a Slack thread.

    Args:
        channel: Channel ID containing the thread
        thread_ts: Timestamp of the parent message
        limit: Maximum replies to return (default 100)
        cursor: Pagination cursor from a previous response
        ctx: MCP context for logging

    Returns:
        List of thread messages with pagination metadata
    """
    client = get_client(ctx)
    try:
        result = await client.get_thread_replies(
            channel=channel, ts=thread_ts, limit=limit, cursor=cursor
        )
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Search Tools
# ============================================================================


@mcp.tool()
async def search_messages(
    query: str,
    count: int = 20,
    sort: str = "timestamp",
    sort_dir: str = "desc",
    cursor: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Search messages across the Slack workspace.

    Args:
        query: Search query string (supports Slack search syntax)
        count: Results per page, max 100 (default 20)
        sort: Sort by "score" (relevance) or "timestamp" (default "timestamp")
        sort_dir: Sort direction "asc" or "desc" (default "desc")
        cursor: Pagination cursor (use "*" for first page with cursor-based pagination)
        ctx: MCP context for logging

    Returns:
        Matching messages with pagination info
    """
    client = get_client(ctx)
    try:
        result = await client.search_messages(
            query=query, count=count, sort=sort, sort_dir=sort_dir, cursor=cursor
        )
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# User Tools
# ============================================================================


@mcp.tool()
async def get_user_info(
    user_id: str,
    ctx: Context | None = None,
) -> dict:
    """Look up a Slack user's profile details.

    Args:
        user_id: The user's ID (e.g. U1234567890)
        ctx: MCP context for logging

    Returns:
        User profile including name, email, timezone, and status
    """
    client = get_client(ctx)
    try:
        result = await client.get_user_info(user=user_id)
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Reaction Tools
# ============================================================================


@mcp.tool()
async def add_reaction(
    channel: str,
    timestamp: str,
    emoji: str,
    ctx: Context | None = None,
) -> dict:
    """Add an emoji reaction to a message.

    Args:
        channel: Channel ID containing the message
        timestamp: Timestamp of the message to react to
        emoji: Emoji name without colons (e.g. "thumbsup", "eyes", "white_check_mark")
        ctx: MCP context for logging

    Returns:
        Confirmation of the reaction
    """
    client = get_client(ctx)
    try:
        result = await client.add_reaction(channel=channel, timestamp=timestamp, name=emoji)
        return result.model_dump(exclude_none=True)
    except SlackAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Resources
# ============================================================================


@mcp.resource("skill://slack/usage")
def skill_usage() -> str:
    """Usage guide for the Slack MCP server tools."""
    return SKILL_CONTENT


# ============================================================================
# Entrypoints
# ============================================================================

# ASGI app for HTTP deployment (uvicorn mcp_slack.server:app)
app = mcp.http_app()

# Stdio entrypoint for Claude Desktop / mpak
if __name__ == "__main__":
    logger.info("Running in stdio mode")
    mcp.run()
