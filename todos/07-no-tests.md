# No Tests

## Issue
No test coverage despite test infrastructure being set up.

## Current State

### Backend
- `service/game/tests.py` contains only boilerplate
- No model tests
- No API tests
- No WebSocket consumer tests
- Django test infrastructure is available

### Frontend
- Vitest configured in `package.json`
- Only `demo.spec.ts` exists (likely boilerplate)
- No component tests
- No WebSocket tests
- No state management tests

## Critical Areas to Test

### Backend Priority
1. **Models**: Score calculation, answer recording
2. **Serializers**: Data format correctness
3. **WebSocket Consumer**: Message routing, state updates
4. **Views**: API endpoints return correct data

### Frontend Priority
1. **WebSocket Client**: Message handling, reconnection
2. **State Management**: Updates propagate correctly
3. **Components**: Board rendering, question display
4. **Score Calculation**: Matches backend

## Benefits of Adding Tests
- Catch regressions during refactoring
- Document expected behavior
- Enable confident changes
- Prevent N+1 queries from creeping back

## Action Items
- [ ] Write model tests for score calculations
- [ ] Add API endpoint tests
- [ ] Test WebSocket message handling
- [ ] Add frontend component tests
- [ ] Test WebSocket client state updates
- [ ] Set up CI to run tests automatically
- [ ] Add coverage reporting
