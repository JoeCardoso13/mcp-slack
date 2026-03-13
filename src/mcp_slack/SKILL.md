# Slack MCP Server — Skill Guide

## Tools

| Tool | Use when... |
|------|-------------|
| `send_message` | You need to post a message to a channel or DM |
| `reply_to_thread` | You need to reply within a specific thread |
| `list_channels` | You need to find channels in the workspace |
| `create_channel` | You need to create a new channel |
| `set_channel_topic` | You need to update a channel's topic |
| `get_channel_history` | You need to read recent messages from a channel |
| `get_thread_replies` | You need to read all replies in a thread |
| `search_messages` | You need to find messages matching a query |
| `get_user_info` | You have a user ID and need their profile details |
| `add_reaction` | You need to react to a message with an emoji |

## Context Reuse

- Use `channel` IDs from `list_channels` when calling other tools
- Use `ts` (timestamp) from messages to reply to threads or add reactions
- Use `user` IDs from messages with `get_user_info` to look up who sent them
- Use `thread_ts` from messages with `reply_count > 0` to read thread replies

## Workflows

### 1. Channel Broadcast
1. `list_channels` to find the target channel
2. `send_message` to post the announcement

### 2. Thread Summarizer
1. `get_channel_history` to find the thread parent message
2. `get_thread_replies` to read all replies
3. `get_user_info` for each participant to add context

### 3. Channel Setup
1. `create_channel` with the desired name
2. `set_channel_topic` to describe the channel's purpose
3. `send_message` to post an introductory message
