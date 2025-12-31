# Generic Message Targeting for WebSocket Relay

## Status

⏳ **PENDING** - Not yet implemented

## Problem

Currently, the WebSocket relay only supports broadcast messaging - all messages sent by any client are relayed to all clients in the game room. There's no way to send a message to a specific client or subset of clients.

This limitation affects:
- **Latency monitoring**: Ping/pong messages flood all clients unnecessarily (see TODO #23 Phase 3)
- **Targeted responses**: Clients cannot respond directly to the sender of a message
- **Private communication**: No way for server to send admin/control messages to specific clients
- **Network efficiency**: Unnecessary message traffic when only one client needs a response
- **Future features**: Hardware-specific commands, client-specific configuration updates, etc.

## Current State

**Backend** (`/home/user/quizzer/service/game/consumers.py`):
- All messages are broadcast to the entire room group (line 74-76)
- No sender identification in relayed messages
- No routing logic based on recipients

```python
async def receive_json(self, content):
    # Simple broadcast relay - no special handling
    await self.channel_layer.group_send(
        self.room_group_name, {"type": "game_message", "message": content}
    )
```

**Frontend** (`/home/user/quizzer/app/src/lib/websocket.ts`):
- Receives all messages sent to the room
- No way to identify which client sent a message
- No way to send messages to specific recipients

## Proposed Solution

Implement a **generic message targeting system** that allows routing messages by:
1. **`channel_id`** (backend-assigned channel address) - Target a specific WebSocket connection
2. **`client_id`** (client-provided identifier) - Target a specific client instance (e.g., "osc-lighting")
3. **`client_type`** (client-provided type) - Target all clients of a type (e.g., all "osc" clients)

### Naming Considerations

**`channel_id` vs `sender_id`:**
- Use **`channel_id`** to make it clear this is a backend-assigned identifier
- Maps directly to Django Channels' `channel_name` (the unique identifier for each WebSocket connection)
- Distinguishes it from client-provided identifiers (`client_id`, `client_type`)
- Makes it clear this is an infrastructure-level address, not a user-facing identifier

**Three types of identifiers:**
1. **`channel_id`** - Backend-assigned, unique per WebSocket connection (e.g., `"specific-channel-12345"`)
2. **`client_id`** - Client-provided, identifies a specific client instance (e.g., `"osc-lighting"`)
3. **`client_type`** - Client-provided, identifies the type of client (e.g., `"buzzer"`, `"osc"`)

### Message Format

Add optional `recipient` field to messages:

```typescript
{
  type: "pong",
  timestamp: 123456789,
  recipient: {
    channel_id: "specific-channel-12345"  // Route to specific backend connection
  }
}

// OR

{
  type: "hardware_command",
  command: "set_brightness",
  value: 80,
  recipient: {
    client_id: "osc-lighting"  // Route to specific client_id
  }
}

// OR

{
  type: "toggle_buzzers",
  enabled: true,
  recipient: {
    client_type: "buzzer"  // Route to all buzzer clients
  }
}

// OR (no recipient = broadcast to all, backward compatible)

{
  type: "select_question",
  question_id: 42
  // No recipient field = broadcast to everyone
}
```

**Rules:**
- `recipient` is optional - messages without it are broadcast to all (backward compatible)
- `recipient` can contain any combination of: `channel_id`, `client_id`, or `client_type`
- If multiple fields are provided, all criteria must match (AND logic)
- In practice, typically only one field is needed, but multiple are allowed for flexibility

### Backend Changes

**Update**: `/home/user/quizzer/service/game/consumers.py`

1. **Add channel_id to all outgoing messages:**

```python
async def game_message(self, event):
    """
    Send message to WebSocket client.

    Injects channel_id into all messages before sending.
    """
    message = event["message"]

    # Inject channel_id so clients know the backend channel address
    # Use channel_name as the unique channel identifier
    message["channel_id"] = self.channel_name

    await self.send_json(message)
```

2. **Implement recipient-based routing:**

**Design Note:** The filtering approach is generic - instead of using separate `filter_client_id` and `filter_client_type` event fields, we pass the entire `recipient` dict. This makes the code cleaner and more extensible for future recipient types.

**Code Style Note:** The code examples below include explanatory comments for documentation purposes. In the actual implementation, omit obvious comments (like `# Don't send - client_id doesn't match`) - the code should be self-explanatory. Only include comments for non-obvious business logic or complex algorithms.

```python
async def receive_json(self, content):
    """
    Relay messages with optional recipient targeting.

    - No recipient: Broadcast to all clients in room
    - recipient.channel_id: Send to specific channel
    - recipient.client_id: Send to all connections with matching client_id
    - recipient.client_type: Send to all connections with matching client_type
    """
    # Basic validation
    if not isinstance(content, dict) or "type" not in content:
        return

    recipient = content.get("recipient")

    # No recipient = broadcast to all (backward compatible)
    if not recipient:
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "game_message", "message": content}
        )
        return

    # Validate recipient format
    if not isinstance(recipient, dict):
        return

    # Route based on recipient type
    if "channel_id" in recipient and len(recipient) == 1:
        # Optimization: direct channel send when only channel_id is specified
        target_channel = recipient["channel_id"]
        await self.channel_layer.send(
            target_channel,
            {"type": "game_message", "message": content}
        )

    else:
        # Filtered broadcast (client_id, client_type, or multiple criteria)
        # Pass recipient dict for generic filtering
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_message",
                "message": content,
                "recipient": recipient  # Pass entire recipient for filtering
            }
        )


async def game_message(self, event):
    """
    Send message to WebSocket client with optional recipient filtering.

    Filters messages based on recipient criteria if present.
    All criteria must match (AND logic).
    """
    message = event["message"]
    recipient = event.get("recipient")

    # Apply recipient filter if present
    if recipient:
        # Generic filter: ALL criteria must match
        if "channel_id" in recipient and self.channel_name != recipient["channel_id"]:
            return

        if "client_id" in recipient and self.client_id != recipient["client_id"]:
            return

        if "client_type" in recipient and self.client_type != recipient["client_type"]:
            return

    # Inject channel_id
    message["channel_id"] = self.channel_name

    await self.send_json(message)
```

### Frontend Changes

**Update**: `/home/user/quizzer/app/src/lib/websocket.ts`

Add helper method for targeted sends:

```typescript
class WebSocketClient {
  // ... existing code

  /**
   * Send a message to a specific recipient
   */
  sendTo(recipient: { channel_id?: string; client_id?: string; client_type?: string }, message: object) {
    this.send({
      ...message,
      recipient
    });
  }

  /**
   * Reply directly to the sender of a message
   */
  replyTo(originalMessage: any, response: object) {
    if (!originalMessage.channel_id) {
      throw new Error("Cannot reply: original message has no channel_id");
    }

    this.sendTo({ channel_id: originalMessage.channel_id }, response);
  }
}
```

Usage example:
```typescript
// Broadcast (existing behavior)
ws.send({ type: "select_question", question_id: 42 });

// Send to specific channel (backend connection)
ws.sendTo({ channel_id: "channel-xyz-12345" }, { type: "pong", timestamp: 123 });

// Send to specific client_id
ws.sendTo({ client_id: "osc-lighting" }, { type: "set_brightness", value: 80 });

// Send to all clients of a type
ws.sendTo({ client_type: "buzzer" }, { type: "toggle_buzzers", enabled: true });

// Reply to a message
ws.on('message', (data) => {
  if (data.type === 'ping') {
    ws.replyTo(data, { type: 'pong', timestamp: data.timestamp });
  }
});
```

## Network Efficiency Benefits

**Example: Ping/Pong with 20 clients**
- Without targeting: 1 ping + (20 pongs × 20 recipients) = **421 messages**
- With targeting: 1 ping + 20 targeted pongs = **21 messages**
- **Reduction: 95%**

## Implementation Phases

### Phase 1: Backend Infrastructure ⏳ PENDING

- [ ] Add `channel_id` injection in `game_message()` handler
- [ ] Implement recipient validation in `receive_json()`
- [ ] Implement `channel_id` direct routing using `channel_layer.send()`
- [ ] Implement `client_id` filtered broadcast
- [ ] Implement `client_type` filtered broadcast
- [ ] Add backend tests for all routing modes
- [ ] Document message format in API docs

### Phase 2: Frontend Support ⏳ PENDING

- [ ] Add TypeScript types for recipient targeting
- [ ] Implement `sendTo()` helper method
- [ ] Implement `replyTo()` helper method
- [ ] Add frontend unit tests for targeting helpers
- [ ] Update documentation with usage examples

### Phase 3: Migration & Integration ⏳ PENDING

- [ ] Update TODO #23 Phase 3 (latency monitoring) to use targeted pong
- [ ] Verify backward compatibility with existing broadcast messages
- [ ] Add E2E tests for multi-client targeted messaging
- [ ] Performance testing with multiple clients

## Dependencies

- No new packages required
- No database changes required
- Fully backward compatible with existing message patterns

## Priority

**High** - Blocks TODO #23 Phase 3 (latency monitoring) and improves scalability for multi-client scenarios

## Related TODOs

- **TODO #23 Phase 3** (Connection Status Overlay - Latency Monitoring) - Will use targeted pong messages
- **TODO #22** (WebSocket ↔ OSC Bridge) - Will benefit from client_type and client_id targeting
