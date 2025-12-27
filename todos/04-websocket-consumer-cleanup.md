# WebSocket Consumer Cleanup

## Current State
`service/game/consumers.py` has three patterns that reflect an incomplete migration:

### Pattern 1: DB Mutation Without Broadcast (lines 43-44)
```python
if content.get('type') == 'toggle_question':
    await self.update_question_status(content['questionId'], content['answered'])
    # No broadcast - bug! Other clients don't see the update
```

### Pattern 2: DB Mutation With Custom Broadcast (lines 46-59)
```python
if content.get('type') == 'record_answer':
    new_score = await self.record_player_answer(...)
    # Custom broadcast with transformed message
    await self.channel_layer.group_send(...)
```

### Pattern 3: Pure Relay (lines 60-67) ✅ KEEP THIS
```python
else:
    # Just forwards message to all clients - this is the GOOD pattern!
    await self.channel_layer.group_send(...)
```

## Architectural Decision

With the hybrid REST + WebSocket architecture, these "inconsistencies" are actually signals:

**Pattern 3 is correct** - This is the elegant relay pattern for coordination messages.
**Patterns 1 & 2 should be removed** - Database mutations should move to REST APIs.

## Migration Plan

### Remove from WebSocket Consumer
- `toggle_question` → Move to `PATCH /api/questions/{id}/`
- `record_answer` → Move to `POST /api/games/{id}/answers/`

These will:
1. Process via REST API
2. Return response to caller
3. Broadcast to WebSocket for sync

### Keep in WebSocket Consumer (Relay Pattern)
- `select_question` - Host navigation
- `reveal_category` - UI animation
- `select_board` - Game flow
- `buzzer_pressed` - Hardware events
- `toggle_buzzers` - Buzzer enable/disable
- Any future coordination messages

## The Clean End State

After migration, the consumer should look like:

```python
async def receive_json(self, content):
    # Pure relay - just forward coordination messages
    await self.channel_layer.group_send(
        self.room_group_name,
        {
            'type': 'game_message',
            'message': content
        }
    )

async def game_message(self, event):
    message = event['message']
    await self.send_json(message)
```

**That's it!** No special cases, no database logic. Just routing.

Database mutations come through REST APIs, which then broadcast via:
```python
# In REST view
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f'board_{board_id}',
    {'type': 'game_message', 'message': {...}}
)
```

## Action Items

- [ ] Implement REST API for `record_answer` (see TODO #11)
- [ ] Implement REST API for `toggle_question` (see TODO #11)
- [ ] Remove database mutation logic from WebSocket consumer
- [ ] Verify relay pattern works for all coordination messages
- [ ] Update frontend to use REST APIs for mutations
- [ ] Keep WebSocket handler purely for coordination

## Benefits of Clean Separation

✅ WebSocket consumer becomes trivial (easy to understand and maintain)
✅ No mixing of concerns (relay vs. persistence)
✅ Can add new coordination features without touching database logic
✅ Database mutations get proper error handling via REST
✅ Clear mental model: "WebSocket = coordination, REST = persistence"

## Note

The "inconsistency" isn't a bug to fix in the consumer - it's a sign that we started with WebSocket-only and need to complete the migration to hybrid architecture. Once complete, the consumer will be beautifully simple.
