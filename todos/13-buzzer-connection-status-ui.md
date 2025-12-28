# Buzzer Connection Status in UI

## Problem
Currently there's no way to see if the hardware buzzer client is connected to the game server. Hosts need a simple visual indicator to know if the buzzers are working.

## Requirements

### Frontend Display
- Simple red/green indicator near the buzzer controls
- Green = buzzer client connected
- Red = no buzzer client connected
- **Host-only visibility** (not shown in spectator view)
- **Clickable** to toggle buzzer client log level (WARN ↔ DEBUG)

### Backend Changes
- Track if a buzzer client WebSocket is currently connected
- Broadcast connection state changes (connected/disconnected) to all clients
- No need to track multiple clients - single buzzer system

### WebSocket Messages

**Server → All Clients (connection state):**
```json
{
  "type": "buzzer_connection_status",
  "connected": true | false
}
```

**Client → Server (relayed to buzzer client):**
```json
{
  "type": "buzzer_set_log_level",
  "level": "DEBUG" | "WARN"
}
```

### Location in UI
- Near existing buzzer enable/disable controls in host view
- Simple status dot or small indicator

## Implementation Tasks
- [ ] Track buzzer client connection in backend WebSocket consumer (service/game/consumers.py)
  - Set flag when client with buzzer role connects
  - Clear flag when buzzer client disconnects
- [ ] Broadcast `buzzer_connection_status` message when state changes
- [ ] Frontend: On receiving `buzzer_connection_status` with `connected=True`:
  - Send current buzzer state (`toggle_buzzers` with current enabled state)
  - Ensures newly connected buzzer client syncs to correct state
- [ ] Add simple status indicator to host UI near buzzer controls
  - Green dot/icon when connected
  - Red dot/icon when disconnected
  - Clickable to toggle log level
- [ ] Implement click handler to send `buzzer_set_log_level` message
  - Toggle between "WARN" and "DEBUG" (hardcoded, not a dropdown)
  - Track current log level state in frontend
- [ ] Backend: Relay `buzzer_set_log_level` messages to buzzer client
- [ ] Hardware client: Handle `buzzer_set_log_level` message
  - Dynamically adjust logging level at runtime
- [ ] Filter indicator to only show in host view (not spectators)
- [ ] Test with actual hardware buzzer client

## Scope Decisions
- **No automatic game manipulation** - just an indicator
- **Single buzzer client** - no need to handle multiples
- **Host-only** - not visible to spectators or players
- **Simple states** - just connected/disconnected (server can't know "reconnecting")
