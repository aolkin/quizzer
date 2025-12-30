# Connection Status Overlay for Host View

## Problem

Currently, the host view has minimal visibility into client connection status:

- **Limited tracking**: Only buzzer connection is tracked (boolean state)
- **Minimal UI**: Small circular indicator in footer only shows buzzer status
- **No client details**: Cannot see which specific clients are connected (no client_id display)
- **No latency info**: No way to diagnose network/WebSocket performance issues
- **Multiple clients invisible**: With OSC bridge and future clients, need to track multiple connections

As the system grows to support multiple hardware clients (GPIO buzzers, OSC bridges, future integrations), the host needs better visibility into the connection health of all clients.

## Current State

**Connection Tracking:**
- **File**: `/home/user/quizzer/app/src/lib/game-state.svelte.ts`
- Only tracks `buzzerConnected: boolean` (line 15)
- Single boolean state, no support for multiple clients

**WebSocket Message Handling:**
- **File**: `/home/user/quizzer/app/src/lib/websocket.ts` (lines 110-118)
- Receives `client_connection_status` messages from backend
- Message includes: `client_type`, `client_id`, `connected`
- Currently only processes `client_type === 'buzzer'`

**UI Display:**
- **File**: `/home/user/quizzer/app/src/lib/components/ScoreFooter.svelte` (lines 61-70)
- Small 8x8 circular indicator in footer
- Green = connected, Red = disconnected
- Only shows buzzer connection status

**Backend Support:**
- **File**: `/home/user/quizzer/service/game/consumers.py` (lines 16-29)
- Already broadcasts `client_connection_status` for all client types
- Includes `client_type` and `client_id` parameters
- No latency/ping mechanism currently exists

## Proposed Solution

Create a **semi-transparent overlay** in the top-right corner of the host view showing:
1. All connected clients (client_type + client_id)
2. Connection status (connected/disconnected with color coding)
3. Optional latency monitoring (round-trip time)
4. Auto-fade behavior when UI elements are "covered"
5. Click-through capability for non-intrusive operation

### Visual Design

```
┌─────────────────────────────────┐
│ 🟢 buzzer (main)         12ms   │
│ 🟢 osc (osc-lighting)    8ms    │
│ 🔴 osc (osc-sound)       --     │
└─────────────────────────────────┘
```

**Characteristics:**
- **Position**: Fixed top-right corner (e.g., `top: 1rem, right: 1rem`)
- **Z-index**: High (e.g., `z-50` or `z-60`) to stay above game UI
- **Transparency**: Semi-transparent background (e.g., `bg-black/50`)
- **Auto-fade**: Increase transparency when hovered or when content beneath needs visibility
- **Click-through**: Use `pointer-events: none` on container, `pointer-events: auto` on interactive elements (if any)
- **Compact**: Small, non-intrusive list format
- **Host-only**: Only visible in host mode

### State Management Updates

**Extend GameStateManager** (`/home/user/quizzer/app/src/lib/game-state.svelte.ts`):

Replace:
```typescript
buzzerConnected = $state(false);
```

With:
```typescript
// Map of client connections: `${client_type}:${client_id}` -> ClientConnection
clientConnections = $state(new Map<string, ClientConnection>());

interface ClientConnection {
  clientType: string;
  clientId: string | null;
  connected: boolean;
  lastSeen: number;  // timestamp
  latency?: number;  // milliseconds (optional)
}
```

**Add methods:**
```typescript
setClientConnection(clientType: string, clientId: string | null, connected: boolean) {
  const key = `${clientType}:${clientId || 'default'}`;
  this.clientConnections.set(key, {
    clientType,
    clientId,
    connected,
    lastSeen: Date.now(),
    latency: this.clientConnections.get(key)?.latency
  });
}

setClientLatency(clientType: string, clientId: string | null, latency: number) {
  const key = `${clientType}:${clientId || 'default'}`;
  const existing = this.clientConnections.get(key);
  if (existing) {
    existing.latency = latency;
    this.clientConnections.set(key, existing);
  }
}

// Keep backwards-compatible getter for buzzer
get buzzerConnected(): boolean {
  for (const [_, client] of this.clientConnections) {
    if (client.clientType === 'buzzer' && client.connected) {
      return true;
    }
  }
  return false;
}
```

### WebSocket Message Handler Updates

**Update** `/home/user/quizzer/app/src/lib/websocket.ts`:

```typescript
} else if (data.type === 'client_connection_status') {
  // Track all client types, not just buzzer
  gameState.setClientConnection(
    data.client_type,
    data.client_id,
    data.connected
  );

  // Keep existing buzzer-specific logic
  if (data.client_type === 'buzzer' && data.connected && this.mode === UiMode.Host) {
    this.toggleBuzzers(gameState.buzzersEnabled);
  }
}
```

### New Component: ConnectionStatusOverlay

**Create**: `/home/user/quizzer/app/src/lib/components/ConnectionStatusOverlay.svelte`

```svelte
<script lang="ts">
  import { type GameStateManager } from '$lib/game-state.svelte';

  interface Props {
    gameState: GameStateManager;
  }

  let { gameState }: Props = $props();

  // Auto-fade on hover
  let isHovered = $state(false);

  // Sort clients: connected first, then by type
  const sortedClients = $derived(
    Array.from(gameState.clientConnections.values())
      .sort((a, b) => {
        if (a.connected !== b.connected) return a.connected ? -1 : 1;
        return a.clientType.localeCompare(b.clientType);
      })
  );
</script>

<div
  class="fixed top-4 right-4 z-50 transition-opacity duration-300 pointer-events-none"
  class:opacity-30={isHovered}
  class:opacity-70={!isHovered}
  onmouseenter={() => isHovered = true}
  onmouseleave={() => isHovered = false}
>
  <div class="bg-surface-800 rounded-lg shadow-lg p-3 min-w-[200px]">
    <h3 class="text-xs font-semibold mb-2 text-surface-300">Clients</h3>

    {#if sortedClients.length === 0}
      <p class="text-xs text-surface-400 italic">No clients connected</p>
    {:else}
      <ul class="space-y-1">
        {#each sortedClients as client}
          <li class="flex items-center justify-between text-xs">
            <div class="flex items-center gap-2">
              <span class="text-lg {client.connected ? 'text-green-500' : 'text-red-500'}">
                {client.connected ? '🟢' : '🔴'}
              </span>
              <span class="text-surface-200">
                {client.clientType}
                {#if client.clientId}
                  <span class="text-surface-400">({client.clientId})</span>
                {/if}
              </span>
            </div>

            {#if client.latency !== undefined}
              <span class="text-surface-400 ml-2">
                {client.latency}ms
              </span>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>
```

### Integration into Host View

**Update**: `/home/user/quizzer/app/src/routes/[game]/[[mode]]/+page.svelte`

Add the overlay component to the host view:
```svelte
{#if mode === UiMode.Host}
  <BoardSelector {gameState} {ws} />
  <ConnectionStatusOverlay {gameState} />
{/if}
```

## Latency Monitoring (Optional Enhancement)

### Design

Add ping/pong mechanism to measure WebSocket round-trip time:

**Frontend sends:**
```json
{
  "type": "ping",
  "timestamp": 1234567890123
}
```

**Backend responds:**
```json
{
  "type": "pong",
  "timestamp": 1234567890123
}
```

**Frontend calculates:**
```typescript
latency = Date.now() - originalTimestamp
```

### Implementation Steps for Latency

#### Backend Changes

**Update**: `/home/user/quizzer/service/game/consumers.py`

Add ping/pong message handling:
```python
async def receive_json(self, content):
    message_type = content.get("type")

    # Handle ping requests
    if message_type == "ping":
        await self.send_json({
            "type": "pong",
            "timestamp": content.get("timestamp")
        })
        return

    # Existing message handling...
```

#### Frontend Changes

**Update**: `/home/user/quizzer/app/src/lib/websocket.ts`

Add ping/pong methods:
```typescript
private pingInterval?: ReturnType<typeof setInterval>;
private pendingPings = new Map<number, { clientType: string, clientId: string | null }>();

// Start pinging all connected clients every 5 seconds
private startLatencyMonitoring() {
  this.pingInterval = setInterval(() => {
    // Only monitor in host mode
    if (this.mode !== UiMode.Host) return;

    // Send ping for each connected client type
    for (const [key, client] of this.gameState.clientConnections) {
      if (!client.connected) continue;

      const timestamp = Date.now();
      this.pendingPings.set(timestamp, {
        clientType: client.clientType,
        clientId: client.clientId
      });

      this.send({
        type: 'ping',
        timestamp,
        target_client_type: client.clientType,
        target_client_id: client.clientId
      });
    }
  }, 5000);
}

// Handle pong responses
private handlePong(data: any) {
  const timestamp = data.timestamp;
  const pending = this.pendingPings.get(timestamp);

  if (pending) {
    const latency = Date.now() - timestamp;
    this.gameState.setClientLatency(
      pending.clientType,
      pending.clientId,
      latency
    );
    this.pendingPings.delete(timestamp);
  }
}
```

Add to message handler:
```typescript
} else if (data.type === 'pong') {
  this.handlePong(data);
}
```

Start monitoring on connection:
```typescript
this.ws.addEventListener('open', () => {
  // ... existing logic
  this.startLatencyMonitoring();
});
```

### Latency Monitoring Considerations

**Challenges:**
- **Targeted pings**: WebSocket is a broadcast system - need to ensure pings go to specific clients
- **Backend relay**: Backend would need to relay ping/pong between web UI and hardware clients
- **Complexity**: Adds message routing complexity to the relay-only backend

**Simplified Alternative:**
- Only measure **web UI ↔ backend** latency (not end-to-end to hardware clients)
- Remove `target_client_type` and `target_client_id` from ping messages
- All clients respond to pings, but only their own latency is tracked

**Recommendation:**
- Start **without** latency monitoring (simpler implementation)
- Add latency monitoring in **Phase 2** if needed for debugging/diagnostics

## Implementation Steps

### Phase 1: Multi-Client Connection Tracking (Core Feature)

- [ ] Update `GameStateManager` in `/home/user/quizzer/app/src/lib/game-state.svelte.ts`:
  - [ ] Replace `buzzerConnected` boolean with `clientConnections` Map
  - [ ] Add `ClientConnection` interface
  - [ ] Add `setClientConnection()` method
  - [ ] Add backwards-compatible `buzzerConnected` getter
- [ ] Update WebSocket handler in `/home/user/quizzer/app/src/lib/websocket.ts`:
  - [ ] Track all `client_connection_status` messages, not just buzzer
  - [ ] Call `gameState.setClientConnection()` for all client types
- [ ] Create `ConnectionStatusOverlay.svelte` component:
  - [ ] Fixed positioning in top-right corner
  - [ ] Semi-transparent background
  - [ ] List all connected clients with status indicators
  - [ ] Green/red color coding for connected/disconnected
  - [ ] Display `client_type` and `client_id`
- [ ] Integrate overlay into host view (`/home/user/quizzer/app/src/routes/[game]/[[mode]]/+page.svelte`)
- [ ] Update `ScoreFooter.svelte` to use new `buzzerConnected` getter (should work without changes)

### Phase 2: Auto-Fade & Click-Through (UX Enhancement)

- [ ] Add hover detection to overlay component
- [ ] Implement opacity transition on hover (fade to more transparent)
- [ ] Add `pointer-events: none` to overlay container
- [ ] Add `pointer-events: auto` to any interactive elements (if needed)
- [ ] Test that game UI beneath is still clickable

### Phase 3: Latency Monitoring (Optional)

- [ ] Add ping/pong message types to backend (`/home/user/quizzer/service/game/consumers.py`)
- [ ] Add `setClientLatency()` method to `GameStateManager`
- [ ] Implement ping interval in WebSocket client
- [ ] Implement pong handler to calculate round-trip time
- [ ] Display latency in overlay component
- [ ] Add latency threshold warnings (e.g., >100ms = yellow, >500ms = red)

### Testing

- [ ] Manual testing with multiple client types:
  - [ ] Web UI (implicit client)
  - [ ] Buzzer hardware client
  - [ ] OSC bridge client (once implemented)
- [ ] Test connection/disconnection events
- [ ] Test overlay positioning and z-index with other UI elements
- [ ] Test auto-fade behavior
- [ ] Test click-through functionality
- [ ] Test backwards compatibility with existing buzzer indicator in footer
- [ ] (If latency added) Test latency measurement accuracy

### Documentation

- [ ] Document `ClientConnection` interface
- [ ] Document state management changes
- [ ] Add screenshot of overlay to README or docs
- [ ] Document how to interpret connection status

## Design Principles

1. **Non-intrusive**: Small, semi-transparent, click-through overlay
2. **Informative**: Shows all client types, not just buzzer
3. **Real-time**: Updates immediately on connection changes
4. **Backwards compatible**: Existing `buzzerConnected` state still works
5. **Host-only**: Connection status only visible to host (not presentation/viewers)
6. **Extensible**: Easy to add new client types without code changes

## UI/UX Considerations

### Auto-Fade Behavior

**Option 1: Hover-based fade**
- Fade to more transparent when mouse hovers over overlay
- Simple to implement, but requires deliberate hover

**Option 2: Proximity-based fade**
- Fade when cursor is near overlay area
- More complex, requires cursor position tracking

**Option 3: Inactivity-based fade**
- Fade after N seconds of no activity
- Most automatic, but may hide info when needed

**Recommendation**: Start with **Option 1 (hover-based)**, simplest and most predictable.

### Click-Through Considerations

**Challenge**: How to make overlay interactive (e.g., click to see details) while also click-through?

**Solution**: Use conditional `pointer-events`:
- Default: `pointer-events: none` (click-through)
- On hover: `pointer-events: auto` (can interact)
- Or: Always click-through, no interactive elements

**Recommendation**: Start with **always click-through**, no interactive elements. Keep it pure status display.

### Color Coding

- **Green (🟢)**: Client connected and healthy
- **Red (🔴)**: Client disconnected
- **Yellow (🟡)**: Connected but high latency (Phase 3, if latency monitoring added)
- **Gray (⚫)**: Unknown/stale status (e.g., no recent heartbeat)

## Dependencies

- No new packages required
- No backend changes required for Phase 1 & 2
- Backend changes required only for Phase 3 (latency monitoring)

## Priority

**Medium-High** - Improves host visibility and debugging, especially as more client types are added (OSC bridge, future integrations).

## Related TODOs

- Related to TODO #22 (WebSocket ↔ OSC Bridge) - will benefit from multi-client tracking
- Complements existing buzzer connection indicator in ScoreFooter
- No dependencies on authentication TODOs (uses existing WebSocket patterns)

## Future Enhancements (Out of Scope)

- **Click to expand**: Show detailed client info (IP address, connect time, message stats)
- **Disconnection alerts**: Audio/visual alert when critical client disconnects
- **Connection history**: Log of connection events with timestamps
- **Manual reconnect trigger**: Button to force client reconnection
- **Client filtering**: Show/hide specific client types in overlay
