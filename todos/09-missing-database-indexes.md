# Missing Database Indexes

## Issue
No explicit indexes on frequently queried fields, relying only on Django's automatic indexes.

## Django Auto-Indexes
Django automatically creates indexes for:
- Primary keys
- Fields with `unique=True`
- ForeignKey fields

## Missing Indexes

### High Priority
1. **`Question.answered`** - Filtered frequently to get unanswered questions
2. **`Player.buzzer`** - Looked up when buzzer pressed
3. **Composite index**: `(Question.category, Question.answered)` - Common query pattern

### Medium Priority
4. **`Board.order`** - Used in ordering
5. **`Category.order`** - Used in ordering
6. **`Question.order`** - Used in ordering

### Low Priority (Already Indexed via FK)
- Foreign keys are automatically indexed
- `unique_together` creates composite indexes

## How to Add
```python
class Question(models.Model):
    # ...
    answered = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['category', 'answered']),
        ]
```

## Impact Analysis Needed
- Current dataset is probably small
- Indexes add write overhead
- Only add if queries are actually slow
- Use Django Debug Toolbar to identify slow queries

## Action Items
- [ ] Profile actual query performance
- [ ] Add `db_index=True` to `Question.answered`
- [ ] Add `db_index=True` to `Player.buzzer`
- [ ] Consider composite index on (category, answered)
- [ ] Create migration for indexes
- [ ] Test query performance before/after
