# Backend Test Coverage

## Issue
No backend test coverage despite Django test infrastructure being set up.

## Current State
- `service/game/tests.py` contains only boilerplate (`# Create your tests here.`)
- No model tests
- No API endpoint tests
- No service layer tests
- No WebSocket consumer tests
- Django test framework is available and ready to use

## Why This Matters
- Service layer functions need tests before being used in REST APIs
- Model score calculations are complex and error-prone
- N+1 query optimizations need verification
- WebSocket relay pattern should be validated
- REST APIs need integration tests

## Priority Areas

### 1. Service Layer (Highest Priority)
Test business logic before REST API implementation:
```python
def test_record_player_answer_new():
    """Test recording a new answer"""
    score = services.record_player_answer(player.id, question.id, True, 400)
    assert score == 400

def test_record_player_answer_correctness_change():
    """Test changing from correct to incorrect"""
    # Initial correct answer
    services.record_player_answer(player.id, question.id, True, 400)
    # Change to incorrect - should delete old answer
    score = services.record_player_answer(player.id, question.id, False, 0)
    assert PlayerAnswer.objects.filter(player=player).count() == 1
```

### 2. Model Tests
```python
def test_player_score_calculation():
    """Verify score property aggregates correctly"""

def test_team_total_score():
    """Verify team score sums all players"""

def test_player_answer_unique_constraint():
    """Can't answer same question twice"""
```

### 3. REST API Tests (After Implementation)
```python
def test_record_answer_success():
    """POST /api/games/{id}/answers/ returns score and version"""

def test_record_answer_invalid_player():
    """Returns 404 for non-existent player"""

def test_record_answer_broadcasts_to_websocket():
    """Verify WebSocket broadcast is sent"""
```

### 4. WebSocket Consumer Tests
```python
def test_relay_pattern():
    """Coordination messages are forwarded unchanged"""

def test_connect_and_join_group():
    """WebSocket connection joins correct channel group"""
```

### 5. Serializer Tests
```python
def test_game_serializer_includes_version():
    """Ensure version numbers are serialized"""

def test_nested_serialization():
    """Boards, teams, players all serialize correctly"""
```

## Test Organization
```
service/game/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_serializers.py
│   ├── test_views.py
│   └── test_consumers.py
```

## Action Items
- [ ] Create tests directory structure
- [ ] Write service layer tests (before REST API implementation)
- [ ] Write model tests for score calculations
- [ ] Write serializer tests
- [ ] Write API endpoint tests (after REST API implementation)
- [ ] Write WebSocket consumer relay tests
- [ ] Add test fixtures for common objects (games, teams, players)
- [ ] Verify N+1 query optimizations with Django Debug Toolbar
- [ ] Add test for version number increments

## Tools & Frameworks
- Django's built-in test framework (`django.test.TestCase`)
- Channels testing utilities for WebSocket consumers
- Factory Boy or fixtures for test data
- Coverage.py for coverage reporting

## Success Criteria
- Service layer has 100% coverage (it's small and critical)
- Models have tests for all computed properties
- REST APIs have integration tests
- WebSocket relay pattern is verified
- CI runs tests on every commit
