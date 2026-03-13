# Slack MCP Server

An MCP (Model Context Protocol) server that provides access to the Slack API, allowing AI assistants to interact with Slack workspaces.

## Features

- Send messages and reply to threads
- List, create, and manage channels
- Search messages and read channel history
- Look up user profiles

## Installation

### Using mpak (Recommended)

```bash
# Configure your Bot Token
mpak config set @joecardoso13/slack api_key=xoxb-your-bot-token

# Run the server
mpak run @joecardoso13/slack
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/JoeCardoso13/mcp-slack.git
cd mcp-slack

# Install dependencies with uv
uv sync

# Set your Bot Token
export SLACK_API_KEY=xoxb-your-bot-token

# Run the server
uv run python -m mcp_slack.server
```

## Configuration

### Getting Your Bot Token

1. Go to https://api.slack.com/apps
2. Create a new app (or select an existing one)
3. Under "OAuth & Permissions", add the required scopes
4. Install the app to your workspace
5. Copy the Bot User OAuth Token (starts with `xoxb-`)

### Claude Desktop Configuration

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "slack": {
      "command": "mpak",
      "args": ["run", "@joecardoso13/slack"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_items` | List items from the API with optional limit |
| `get_item` | Get a single item by its ID |

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run ty check src/

# Run all checks
make check
```

## License

MIT
