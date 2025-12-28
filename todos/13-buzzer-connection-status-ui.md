# Buzzer Connection Status in UI

## Problem
Currently there's no way to see if the hardware buzzer client is connected to the game server. When the buzzer script disconnects/reconnects, players and hosts have no visibility into whether buzzers are actually working.

## Requirements

### Frontend Display
- Show connection status indicator for buzzer client(s)
- Display states: Connected, Disconnected, Reconnecting
- Show last connection time / last heartbeat
- Visual indicator (green dot = connected, red = disconnected, yellow = reconnecting)
- Should be visible to host (maybe spectator view too)

### Backend Changes
- Track buzzer client connection state in WebSocket consumer
- Broadcast connection state changes to all clients
- Include connection metadata (last seen, client ID, etc.)

### WebSocket Messages

**New message type (Server → All Clients):**
```json
{
  "type": "buzzer_connection_status",
  "status": "connected" | "disconnected" | "reconnecting",
  "lastSeen": "2024-01-15T10:30:00Z",
  "clientId": "buzzer-client-1"  // Optional: for multi-buzzer setups
}
```

### Location in UI
Options to consider:
- Status bar at top/bottom of game view
- Settings/debug panel
- Always visible vs. collapsed indicator
- Host-only vs. visible to all

## Implementation Tasks
- [ ] Add connection state tracking to backend WebSocket consumer
- [ ] Broadcast connection status changes when client connects/disconnects
- [ ] Add frontend component to display connection status
- [ ] Style visual indicator (connected/disconnected/reconnecting states)
- [ ] Add timestamp display for last connection event
- [ ] Test with actual hardware buzzer client
- [ ] Consider adding connection history/log for debugging

## Nice-to-Have Features
- Sound/notification when buzzer disconnects during active game
- Auto-disable questions when buzzer disconnects
- Connection quality indicator (latency, packet loss)
- Support for multiple buzzer clients (show each separately)
- Reconnection attempt counter

## Open Questions
- Should this be visible to players, or host-only?
- Should we pause/disable the game automatically when buzzer disconnects?
- How to handle multiple buzzer clients (if that's a future feature)?
- Should we show this on spectator view?
