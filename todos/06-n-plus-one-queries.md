# N+1 Query Problems

## Issue
Model properties trigger database queries in loops, causing performance issues.

## Problems

### 1. Player Score Property (`models.py:93-95`)
```python
@property
def score(self):
    return sum(answer.points if answer.points is not None else answer.question.points
               for answer in self.answers.all())
```
- Queries database every time `.score` is accessed
- Not cached
- If accessing 10 players, triggers 10+ queries

### 2. Team Total Score (`models.py:83-84`)
```python
@property
def total_score(self):
    return sum(player.score for player in self.players.all())
```
- Calls `player.score` for each player
- Compounds the problem above
- For team with 4 players: 1 query for players + 4 queries for scores = 5 queries per team

### 3. Serializer Usage
`serializers.py:34` includes `score` in `PlayerSerializer`, triggering queries during API calls.

## Example Impact
Loading a game with 4 teams, 4 players each:
- 1 query for game
- 4 queries for teams
- 16 queries for players
- 16 queries for player answers
- Plus queries for questions referenced in answers
- **40+ queries instead of 3-4!**

## Solutions

### Option 1: Annotate in QuerySets
```python
from django.db.models import Sum, Q

Player.objects.annotate(
    score=Sum('answers__points',
              default=0,
              filter=Q(answers__points__isnull=False))
)
```

### Option 2: Cache in Serializer
Override `to_representation()` to prefetch and cache.

### Option 3: Denormalize
Add `score` field to model, update on answer changes.

## Recommendation
Use Option 1 for read operations, keep property for convenience.

## Action Items
- [ ] Add annotate queries in views/serializers
- [ ] Remove score from serialized fields or compute efficiently
- [ ] Add `select_related` and `prefetch_related` to views
- [ ] Consider adding indexes on foreign keys
- [ ] Test with Django Debug Toolbar to verify query count
