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
Extract business logic to a new `service/game/services.py` as **module functions** (not a class with staticmethods):

```python
# services.py
from django.db import transaction

def update_question_status(question_id: int, answered: bool) -> None:
    """Toggle question answered status"""
    Question.objects.filter(id=question_id).update(answered=answered)

@transaction.atomic
def record_player_answer(player_id: int, question_id: int, is_correct: bool, points: int = None) -> int:
    """Record a player's answer and return updated score"""
    # Multi-step business logic with proper transaction handling
    # ...
    return player.score
```

**Why module functions instead of a class?**
- No need for class wrapper - just use functions
- Simpler imports: `from . import services; services.record_answer(...)`
- Can add `@transaction.atomic` for proper atomicity
- More Pythonic for stateless operations

## Benefits
- Testable business logic without WebSocket infrastructure
- Reusable from REST API views, admin actions, management commands
- Cleaner WebSocket consumer focused on message routing
- Proper transaction handling and error boundaries
- Easier to add validation

## Action Items
- [ ] Create `service/game/services.py`
- [ ] Extract `record_player_answer` logic to service
- [ ] Extract `update_question_status` logic to service
- [ ] Update consumer to use service methods
- [ ] Add unit tests for service methods
