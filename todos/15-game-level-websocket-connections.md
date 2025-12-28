# Game-Level WebSocket Connections for Buzzer Clients

## Problem

Currently, WebSocket connections are scoped to individual **boards**, but games can have multiple boards (Round 1, Round 2, etc.). This creates inconvenience:

- **Teams/Players belong to the Game**, not a specific board
- **Buzzer clients connect to a board-specific WebSocket** (`/ws/game/{board_id}/`)
- When the host switches boards during a game, the hardware buzzer client must be **manually restarted** with the new board ID
- This breaks the flow of multi-round games

## Current Architecture

```
Game
├── Board 1 (WebSocket: /ws/game/1/)
│   ├── Categories
│   └── Questions
├── Board 2 (WebSocket: /ws/game/2/)
│   ├── Categories
│   └── Questions
└── Teams/Players (shared across all boards)
```

**Issue**: Buzzer hardware connects to board-specific WebSocket, but buzzers are logically scoped to the Game (they're associated with players, who belong to the game).

## Proposed Solutions

### Option 1: Game-Level WebSocket Endpoint (Recommended)
Create a new WebSocket endpoint at the game level:
- `/ws/game/{board_id}/` - Current board-scoped endpoint (keep for backwards compatibility)
- `/ws/game-session/{game_id}/` - New game-scoped endpoint

**Game-scoped behavior:**
- Clients connect to game, not specific board
- Backend tracks "active board" per game via `select_board` messages
- Buzzer client stays connected across board switches
- Backend routes board-specific messages to the active board's room

### Option 2: Smart Buzzer Client Board Switching
Make the buzzer client handle `select_board` messages:
- When host sends `select_board`, buzzer client receives it
- Buzzer client disconnects from old board WebSocket
- Buzzer client reconnects to new board WebSocket automatically

**Pros**: No backend changes needed
**Cons**: Creates brief disconnection during board switch, more complex client logic

### Option 3: Document Current Limitation
Accept that buzzer clients are board-scoped:
- Document that hardware must be restarted when switching boards
- Add helper script to make restarting easier

**Pros**: Simplest, no code changes
**Cons**: Poor UX for multi-board games

## Recommendation

**Option 1** is the best long-term solution because:
- Matches the logical model (buzzers belong to game, not board)
- No manual intervention required
- Cleaner architecture
- Enables future features (cross-board stats, persistent connections)

However, it requires significant refactoring of the WebSocket architecture.

## Implementation Notes

If implementing Option 1:
- Keep board-level endpoints for backward compatibility
- Create new `GameSessionConsumer` for game-level connections
- Add `active_board_id` tracking per game session
- Route messages appropriately based on message type and active board

## Priority

**Medium** - Current workaround (restarting buzzers) is functional but inconvenient. Not blocking core functionality.
