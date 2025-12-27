# WebSocket Consumer Has Business Logic

## Issue
`service/game/consumers.py` mixes WebSocket protocol handling with database operations and business logic.

## Problems
- `record_player_answer()` method (lines 30-40) has complex business logic:
  - Conditional delete based on correctness change
  - Conditional update based on points change
  - Score calculation
- Violates single responsibility principle
- Hard to test in isolation
- Can't reuse logic outside WebSocket context

## Proposed Solution
Extract business logic to a new `service/game/services.py`:

```python
# services.py
class GameService:
    @staticmethod
    def record_answer(player_id, question_id, is_correct, points):
        """Record a player's answer and return updated score"""
        # Business logic here

    @staticmethod
    def toggle_question_status(question_id, answered):
        """Toggle question answered status"""
        # Logic here
```

## Benefits
- Testable business logic
- Reusable in API views or admin actions
- Cleaner WebSocket consumer focused on message routing
- Easier to add validation and error handling

## Action Items
- [ ] Create `service/game/services.py`
- [ ] Extract `record_player_answer` logic to service
- [ ] Extract `update_question_status` logic to service
- [ ] Update consumer to use service methods
- [ ] Add unit tests for service methods
