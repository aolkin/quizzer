# Connection Status Overlay for Host View

## Status

**Phase 1 (Multi-Client Connection Tracking): ✅ COMPLETED**
**Phase 2 (Auto-Fade & Click-Through): ✅ COMPLETED**
**Phase 3 (Latency Monitoring): ⏳ PENDING**

### What's Implemented

✅ Multi-client connection tracking with `clientConnections` Map
✅ `ClientConnection` interface with metadata (type, id, connected, lastSeen, latency placeholder)
✅ `ConnectionStatusOverlay.svelte` component with all visual features
✅ Integration into host view (host-only visibility)
✅ Color-coded status indicators (🟢 connected / 🔴 disconnected)
✅ Auto-fade on hover (CSS-based)
✅ Click-through overlay (`pointer-events: none`)
✅ ScoreFooter updated to use `clientConnections` directly
✅ Unit and E2E tests

### What's Remaining

⏳ **Phase 3: Latency Monitoring** - Requires:
- Backend changes to inject `sender_id` and handle ping/pong messages
- Frontend ping interval and pong response handler
- Display latency values in overlay
- This should be implemented after TODO #24 (Hardware WebSocket Client Library)

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

Add ping/pong mechanism to measure WebSocket round-trip time from host to all clients.

**Architecture:**
1. **Host broadcasts ping** - Sent to server, relayed to all clients
2. **All clients respond with pong** - Including the host itself
3. **Host receives all pongs** - Calculates round-trip latency to each client
4. **Server adds sender_id** - Automatic identifier for message routing (separate from custom `client_id`)
5. **Targeted pong responses** - Clients address pong to specific sender to reduce network noise

**Message Flow:**
```
Host → Server: {type: "ping", timestamp: 123, sender_id: "auto-xyz"}
Server → All Clients: (broadcast with sender_id preserved)

Client A → Server: {type: "pong", timestamp: 123, target_sender_id: "auto-xyz"}
Server → Host only: (targeted delivery)

Client B → Server: {type: "pong", timestamp: 123, target_sender_id: "auto-xyz"}
Server → Host only: (targeted delivery)

Host → Server: {type: "pong", timestamp: 123, target_sender_id: "auto-xyz"}
Server → Host only: (host measures its own latency to server)
```

**Benefits:**
- Single ping broadcast measures latency to all clients
- Host can measure its own backend latency
- Reduced network noise via targeted pong delivery
- Leverages existing relay/broadcast architecture

### Backend Changes Required

#### 1. Add sender_id to All Messages

**Update**: `/home/user/quizzer/service/game/consumers.py`

Add `sender_id` to connection state and inject into all messages:
```python
class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # ... existing connection logic

        # Generate unique sender_id for this WebSocket connection
        self.sender_id = f"sender-{self.channel_name}"

        await self.accept()
        # ... rest of existing logic

    async def receive_json(self, content):
        message_type = content.get("type")

        # Add sender_id to all incoming messages before relaying
        content["sender_id"] = self.sender_id

        # Handle pong with targeted delivery
        if message_type == "pong":
            target_sender_id = content.get("target_sender_id")

            if target_sender_id:
                # Targeted delivery: send only to specific sender
                await self.channel_layer.send(
                    target_sender_id.replace("sender-", ""),  # Extract channel name
                    {
                        "type": "relay_message",
                        "message": content
                    }
                )
            else:
                # No target: broadcast to all (fallback)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "relay_message", "message": content}
                )
            return

        # All other messages: relay to group as usual
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "relay_message", "message": content}
        )

    async def relay_message(self, event):
        """Send message to WebSocket"""
        await self.send_json(event["message"])
```

#### 2. Channel Layer Direct Messaging

The above code uses `channel_layer.send()` for targeted delivery to a specific channel (sender).

**Key Insight:**
- `sender_id = "sender-{channel_name}"` uniquely identifies each WebSocket connection
- `channel_layer.send(channel_name, ...)` sends to specific connection
- `channel_layer.group_send(group, ...)` broadcasts to all in group

### Frontend Changes Required

#### State Management

**Update**: `/home/user/quizzer/app/src/lib/game-state.svelte.ts`

Add sender tracking:
```typescript
interface ClientConnection {
  clientType: string;
  clientId: string | null;
  senderId?: string;      // Add sender_id from server
  connected: boolean;
  lastSeen: number;
  latency?: number;
}

setClientConnection(
  clientType: string,
  clientId: string | null,
  connected: boolean,
  senderId?: string        // Add parameter
) {
  const key = `${clientType}:${clientId || 'default'}`;
  this.clientConnections.set(key, {
    clientType,
    clientId,
    senderId,            // Store sender_id
    connected,
    lastSeen: Date.now(),
    latency: this.clientConnections.get(key)?.latency
  });
}
```

#### WebSocket Handler Updates

**Update**: `/home/user/quizzer/app/src/lib/websocket.ts`

Add latency monitoring:
```typescript
private pingInterval?: ReturnType<typeof setInterval>;
private pendingPings = new Map<number, number>();  // timestamp -> sentTime
private hostSenderId?: string;  // Store our own sender_id

// Start pinging all connected clients every 5 seconds
private startLatencyMonitoring() {
  this.pingInterval = setInterval(() => {
    // Only monitor in host mode
    if (this.mode !== UiMode.Host) return;

    const timestamp = Date.now();
    this.pendingPings.set(timestamp, timestamp);

    // Single ping broadcast - all clients will respond
    this.send({
      type: 'ping',
      timestamp
    });
  }, 5000);
}

// Handle incoming messages
private handleMessage(data: any) {
  // Extract and store our own sender_id from any message we receive
  if (data.sender_id && !this.hostSenderId) {
    this.hostSenderId = data.sender_id;
  }

  // Track sender_id for connection status
  if (data.type === 'client_connection_status') {
    this.gameState.setClientConnection(
      data.client_type,
      data.client_id,
      data.connected,
      data.sender_id  // Pass sender_id
    );
    // ... existing buzzer logic
  }

  // Handle ping requests (respond with pong)
  else if (data.type === 'ping') {
    // Respond with pong, targeting the original sender
    this.send({
      type: 'pong',
      timestamp: data.timestamp,
      target_sender_id: data.sender_id  // Target the ping sender
    });
  }

  // Handle pong responses (only in host mode)
  else if (data.type === 'pong' && this.mode === UiMode.Host) {
    const timestamp = data.timestamp;
    const sentTime = this.pendingPings.get(timestamp);

    if (sentTime) {
      const latency = Date.now() - sentTime;
      const respondingSenderId = data.sender_id;

      // Find which client this pong is from by sender_id
      for (const [key, client] of this.gameState.clientConnections) {
        if (client.senderId === respondingSenderId) {
          this.gameState.setClientLatency(
            client.clientType,
            client.clientId,
            latency
          );
          break;
        }
      }

      // If pong is from ourselves (host), track our own latency
      if (respondingSenderId === this.hostSenderId) {
        // Could store in separate state or add "host" to clientConnections
        // For now, log it or add to overlay as special entry
        console.log(`Host latency: ${latency}ms`);
      }
    }
  }

  // ... existing message handlers
}

// Start monitoring on connection
this.ws.addEventListener('open', () => {
  // ... existing logic
  if (this.mode === UiMode.Host) {
    this.startLatencyMonitoring();
  }
});
```

#### Optional: Show Host Latency in Overlay

Add host's own latency to the overlay:
```svelte
<!-- In ConnectionStatusOverlay.svelte -->
<ul class="space-y-1">
  <!-- Show host's own latency first -->
  <li class="flex items-center justify-between text-xs">
    <div class="flex items-center gap-2">
      <span class="text-lg text-blue-500">🔵</span>
      <span class="text-surface-200">Host (this client)</span>
    </div>
    {#if hostLatency !== undefined}
      <span class="text-surface-400 ml-2">{hostLatency}ms</span>
    {/if}
  </li>

  <!-- Then show all other clients -->
  {#each sortedClients as client}
    <!-- ... existing client display -->
  {/each}
</ul>
```

### Network Noise Reduction

**Without targeted pong:**
- Host pings → relayed to N clients
- N clients pong → relayed to N clients (including host)
- Total: 1 + N² messages

**With targeted pong (target_sender_id):**
- Host pings → relayed to N clients
- N clients pong → each delivered only to host
- Total: 1 + N + N = 2N + 1 messages

**Example with 5 clients:**
- Without targeting: 1 + 25 = **26 messages**
- With targeting: 1 + 5 + 5 = **11 messages**
- Savings: **58% reduction**

### Implementation Considerations

**Pros:**
- Single broadcast ping measures all client latencies
- Host can measure its own server latency
- Reduced network noise with targeted pong
- Works with existing relay architecture

**Cons:**
- Requires backend changes (sender_id injection, targeted delivery)
- More complex than simple request/response
- Latency includes server relay time (not just network)

**Recommendation:**
- Implement as **Phase 3** after core overlay is working
- Start with broadcast pong (simpler), add targeting later if noise is an issue
- Consider making ping interval configurable (default 5s, increase to 10s if too noisy)

## Implementation Steps

### Phase 1: Multi-Client Connection Tracking (Core Feature) ✅ COMPLETED

- [x] Update `GameStateManager` in `/home/user/quizzer/app/src/lib/game-state.svelte.ts`:
  - [x] Replace `buzzerConnected` boolean with `clientConnections` Map
  - [x] Add `ClientConnection` interface
  - [x] Add `setClientConnection()` method
  - [x] ~~Add backwards-compatible `buzzerConnected` getter~~ (removed - ScoreFooter updated to use `clientConnections` directly)
- [x] Update WebSocket handler in `/home/user/quizzer/app/src/lib/websocket.ts`:
  - [x] Track all `client_connection_status` messages, not just buzzer
  - [x] Call `gameState.setClientConnection()` for all client types
- [x] Create `ConnectionStatusOverlay.svelte` component:
  - [x] Fixed positioning in top-right corner
  - [x] Semi-transparent background
  - [x] List all connected clients with status indicators
  - [x] Green/red color coding for connected/disconnected
  - [x] Display `client_type` and `client_id`
- [x] Integrate overlay into host view (`/home/user/quizzer/app/src/routes/[game]/[[mode]]/+page.svelte`)
- [x] Update `ScoreFooter.svelte` to use `clientConnections` directly with derived value

### Phase 2: Auto-Fade & Click-Through (UX Enhancement) ✅ COMPLETED

- [x] Add hover detection to overlay component (CSS-based)
- [x] Implement opacity transition on hover (fade to more transparent)
- [x] Add `pointer-events: none` to overlay container
- [x] Test that game UI beneath is still clickable

### Phase 3: Latency Monitoring (Optional) ⏳ PENDING

- [ ] Add ping/pong message types to backend (`/home/user/quizzer/service/game/consumers.py`)
- [ ] Add `setClientLatency()` method to `GameStateManager`
- [ ] Implement ping interval in WebSocket client
- [ ] Implement pong handler to calculate round-trip time
- [ ] Display latency in overlay component
- [ ] Add latency threshold warnings (e.g., >100ms = yellow, >500ms = red)

### Testing

- [x] Manual testing with multiple client types:
  - [x] Web UI (implicit client)
  - [x] Buzzer hardware client
  - [ ] OSC bridge client (once implemented - see TODO #22)
- [x] Test connection/disconnection events
- [x] Test overlay positioning and z-index with other UI elements
- [x] Test auto-fade behavior
- [x] Test click-through functionality
- [x] Test ScoreFooter buzzer indicator with new clientConnections structure
- [x] Added E2E test validation for overlay visibility
- [ ] (Phase 3) Test latency measurement accuracy

### Documentation

- [ ] Document `ClientConnection` interface
- [ ] Document state management changes
- [ ] Add screenshot of overlay to README or docs
- [ ] Document how to interpret connection status

## Design Principles (Implemented)

1. **Non-intrusive**: Small, semi-transparent, click-through overlay ✅
2. **Informative**: Shows all client types, not just buzzer ✅
3. **Real-time**: Updates immediately on connection changes ✅
4. **Direct access**: ScoreFooter uses `clientConnections` directly with derived value ✅
5. **Host-only**: Connection status only visible to host (not presentation/viewers) ✅
6. **Extensible**: Easy to add new client types without code changes ✅

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
- Backend changes required only for Phase 3 (latency monitoring):
  - Sender ID injection in backend
  - Targeted pong delivery
  - **TODO #24** (Hardware WebSocket Client Library) should be updated to support ping/pong

## Priority

**Medium-High** - Improves host visibility and debugging, especially as more client types are added (OSC bridge, future integrations).

Phase 1 & 2 can be implemented independently. Phase 3 (latency) should be implemented **after TODO #24** so hardware clients get ping/pong support.

## Related TODOs

- **TODO #24** (Hardware WebSocket Client Library) - Should implement ping/pong handling for Phase 3
- **TODO #22** (WebSocket ↔ OSC Bridge) - Will benefit from multi-client tracking
- Complements existing buzzer connection indicator in ScoreFooter
- No dependencies on authentication TODOs (uses existing WebSocket patterns)

## Future Enhancements (Out of Scope)

- **Click to expand**: Show detailed client info (IP address, connect time, message stats)
- **Disconnection alerts**: Audio/visual alert when critical client disconnects
- **Connection history**: Log of connection events with timestamps
- **Manual reconnect trigger**: Button to force client reconnection
- **Client filtering**: Show/hide specific client types in overlay
