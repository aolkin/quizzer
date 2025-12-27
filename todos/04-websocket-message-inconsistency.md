# Inconsistent WebSocket Message Handling

## Issue
`service/game/consumers.py` has three different patterns for handling messages:

### Pattern 1: Update DB, Don't Broadcast (lines 43-44)
```python
if content.get('type') == 'toggle_question':
    await self.update_question_status(content['questionId'], content['answered'])
    # No broadcast - other clients don't know!
```

### Pattern 2: Update DB, Broadcast Different Message (lines 46-59)
```python
if content.get('type') == 'record_answer':
    new_score = await self.record_player_answer(...)
    # Broadcasts score update but NOT the original answer event
    await self.channel_layer.group_send(...)
```

### Pattern 3: Just Broadcast (lines 60-67)
```python
else:
    # Broadcasts original message as-is
    await self.channel_layer.group_send(...)
```

## Problems
- Clients sending `toggle_question` won't see updates from other clients
- `record_answer` clients don't get full answer details, just score
- Confusing control flow with if/elif/else
- No clear pattern for when to broadcast what

## Proposed Solution
Standardize on a pattern:
1. Validate incoming message
2. Perform business logic (via service layer)
3. Always broadcast result to all clients
4. Use consistent message format

## Action Items
- [ ] Document message handling pattern
- [ ] Fix `toggle_question` to broadcast state change
- [ ] Make `record_answer` broadcast full answer event
- [ ] Refactor to consistent if/elif chain (no bare else)
- [ ] Add message type validation
