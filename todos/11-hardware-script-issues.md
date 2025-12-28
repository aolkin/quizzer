# Hardware Script Issues

## Issues in `hardware/buzzers.py`

### 1. Broken Reconnection Logic (lines 99-104)
```python
except websockets.ConnectionClosed:
    print("Disconnected")
    exit(1)  # ← This exits the program!
    await asyncio.sleep(1)  # ← Unreachable (dead code)
    await self.connect(True)  # ← Unreachable
    return
```
The `exit(1)` call makes reconnection impossible.

### 2. Hardcoded Server URL (line 75)
```python
uri = f"ws://quasar.local:8000/ws/game/{self.game_id}/"
```
Should be configurable via environment variable or command-line argument.

### 3. No Graceful Shutdown
- GPIO cleanup only happens on KeyboardInterrupt
- No signal handling for SIGTERM
- Could leave GPIO pins in bad state

### 4. No Connection Health Checks
- No ping/pong to detect stale connections
- Could sit "connected" to dead socket
- No timeout handling
- Buzzers stay enabled even when disconnected

### 5. Debug Code Left In *(Keeping as-is)*
- Line 14: `# gc.disable()` commented out
- Lines 42, 49: Debug print statements
- Line 51: Magic number calculations without explanation
- **Decision**: Leaving debug code in place for development/troubleshooting

## Proposed Fixes

### Priority 1: Fix Reconnection
```python
except websockets.ConnectionClosed:
    print("Disconnected, reconnecting...")
    await asyncio.sleep(1)
    await self.connect(reconnect=True)
    return
```

### Priority 2: Make URL Configurable
```python
import os
# Keep quasar.local:8000 as default fallback
SERVER_URL = os.getenv('QUIZZER_SERVER', 'quasar.local:8000')
uri = f"ws://{SERVER_URL}/ws/game/{self.game_id}/"
```
Could also add command-line argument: `--server SERVER_URL`

### Priority 3: Graceful Shutdown
```python
import signal

def cleanup_handler(signum, frame):
    gpio.cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup_handler)
signal.signal(signal.SIGINT, cleanup_handler)
```

## Action Items
- [x] Remove `exit(1)` call, fix reconnection *(Completed)*
- [ ] Add server URL configuration (env var + CLI arg, default to `quasar.local:8000`)
- [ ] Add signal handlers for graceful shutdown (SIGTERM + SIGINT)
- [ ] Add WebSocket ping/pong heartbeat (built-in websockets library support)
  - Add `ping_interval=15` and `ping_timeout=5` to `websockets.connect()`
  - No separate tasks/threads needed - library handles it automatically
  - Force buzzers to disabled state when connection drops (set `self.buzzers.enabled = False`)
- [ ] Replace print() with logging module (support dynamic log level via env/CLI)
  - Use `QUIZZER_LOG_LEVEL` env var or `--log-level` CLI argument
  - Enables runtime control: DEBUG, INFO, WARNING, ERROR
- [ ] Complete hardware documentation in README (expand wiring details)
- [x] Add requirements.txt for hardware dependencies *(Completed)*

## Decisions
- **Debug code**: Keeping commented code and debug statements in place for development
- **Default URL**: Keep `quasar.local:8000` as fallback when making URL configurable
