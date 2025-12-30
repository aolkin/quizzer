# WebSocket ↔ OSC Bridge for Hardware Integration

## Problem

Currently, hardware integration is limited to custom WebSocket clients (like `/hardware/buzzers.py`). This creates barriers for:

- **OSC-based hardware** (lighting controllers, MIDI devices, DMX fixtures)
- **Professional A/V software** (QLab, Resolume, Isadora, TouchDesigner)
- **Control surfaces** (TouchOSC, Lemur, MIDI controllers with OSC support)
- **Home automation** systems with OSC bridges (KNX, DMX)
- **Custom hardware** that uses OSC as a standard protocol

OSC (Open Sound Control) is a widely-supported protocol in live performance, theater tech, and A/V installations. Many production environments already have OSC infrastructure that could integrate with the quizzer application.

## Current State

Hardware integration requires implementing a custom WebSocket client:
- Must handle WebSocket connection management
- Must implement game-specific message protocol
- Must handle reconnection logic
- Example: `/hardware/buzzers.py` (GPIO-based hardware client)

**Issue**: No bridge exists for OSC-based hardware and software.

## Proposed Solution

Create a standalone **WebSocket ↔ OSC bridge** service that:
1. Connects to quizzer backend as a WebSocket client
2. Listens for incoming OSC messages from external hardware/software
3. Translates messages bidirectionally based on configuration
4. Sends OSC commands to external systems based on WebSocket events

### Architecture

```
External OSC Hardware/Software
         ↕ (OSC over UDP)
    OSC Bridge Service
         ↕ (WebSocket)
  Quizzer Backend (Django Channels)
         ↕ (WebSocket)
    Web UI / Other Clients
```

## Implementation Design

### Bridge Service Location
`/hardware/osc_bridge.py` - Standalone Python script, similar to `/hardware/buzzers.py`

### WebSocket Client Component

Connect to quizzer backend with **both** `client_type` AND `client_id`:

```python
ws_url = f"ws://{host}/ws/game/{game_id}/?client_type=osc&client_id={client_id}"
```

**Parameters:**
- `client_type`: `"osc"` - Identifies this as an OSC bridge client
- `client_id`: Unique identifier for this bridge instance (e.g., `"osc-main"`, `"osc-lighting"`)
  - Allows multiple OSC bridges per game
  - Enables different bridges for different purposes (buzzers vs lighting vs sound)
  - Frontend can track connection status per bridge instance

**Messages to Handle (WebSocket → OSC):**
- `toggle_buzzers` → Send OSC command to enable/disable buzzer hardware
- `select_question` → Trigger lighting cue or visual effect
- `buzzer_pressed` → Forward buzzer events to OSC-based sound/lighting
- `select_board` → Update display hardware via OSC
- Any future game events that need hardware control

**Messages to Send (OSC → WebSocket):**
- `buzzer_pressed` - From OSC-based buzzer hardware
- Future: custom game control events

### OSC Server Component

Listen for incoming OSC messages on configurable UDP port:
- Default port: `7400` (or configurable)
- Listen address: `0.0.0.0` (all interfaces)
- Handle OSC bundles and individual messages

### OSC Client Component

Send OSC messages to external systems:
- Configurable destination hosts and ports
- Support multiple OSC destinations per event
- Handle OSC bundle creation for grouped messages

## Configuration Format

Use YAML for configuration (easier to read than JSON for this use case):

```yaml
# Connection settings
websocket:
  host: "localhost:8000"
  game_id: 1
  client_type: "osc"
  client_id: "osc-main"  # Unique identifier for this bridge instance

osc:
  listen_host: "0.0.0.0"
  listen_port: 7400

# WebSocket → OSC mappings (outgoing)
outgoing:
  # Example: Toggle buzzers
  - websocket_type: "toggle_buzzers"
    osc_destinations:
      - host: "192.168.1.100"
        port: 53000
        address: "/quizzer/buzzers/state"
        # Map WebSocket message fields to OSC arguments
        args:
          - field: "enabled"      # WebSocket field name
            type: "int"           # OSC type: int, float, string, bool
            # Optional transform: true→1, false→0

  # Example: Question selection triggers lighting cue
  - websocket_type: "select_question"
    osc_destinations:
      - host: "192.168.1.101"
        port: 53001
        address: "/qlabs/cue/fire"
        args:
          - field: "question"
            type: "int"

  # Example: Send buzzer press to sound system
  - websocket_type: "buzzer_pressed"
    osc_destinations:
      - host: "192.168.1.102"
        port: 9000
        address: "/sound/buzzer"
        args:
          - field: "buzzerId"
            type: "int"

# OSC → WebSocket mappings (incoming)
incoming:
  # Example: OSC buzzer controller sends button presses
  - osc_address: "/buzzer/press"
    websocket_type: "buzzer_pressed"
    # Map OSC arguments to WebSocket message fields
    args:
      - osc_index: 0              # First OSC argument
        websocket_field: "buzzerId"
        type: "int"

  # Example: OSC fader controls buzzer enable state
  - osc_address: "/control/buzzers"
    websocket_type: "toggle_buzzers"
    args:
      - osc_index: 0
        websocket_field: "enabled"
        type: "bool"
        # Optional transform: >0.5 → true, <=0.5 → false
```

### Configuration Notes

**OSC Address Field:**
- Use literal OSC addresses (e.g., `/quizzer/buzzers/state`)
- NO interpolation/substitution in addresses (keep it simple)
- Use OSC arguments for dynamic values

**Why No Address Interpolation:**
- OSC addresses are typically static patterns
- Dynamic data goes in OSC arguments (this is OSC best practice)
- Simpler implementation, easier to debug
- Example: `/quizzer/buzzers/state` with arg `[1]` or `[0]`
  - NOT: `/quizzer/buzzers/{enabled}` (confusing, non-standard)

**Type Conversions:**
- `bool` → `int`: true=1, false=0 (standard OSC convention)
- `int` → `float`: automatic promotion
- `string`: pass through
- `null`/`undefined`: skip argument or use default

## Implementation Steps

### Phase 1: Core Bridge
- [ ] Install `python-osc` library: `pip install python-osc`
- [ ] Create `/hardware/osc_bridge.py` skeleton
- [ ] Implement WebSocket client component (reuse pattern from `/hardware/buzzers.py`)
  - Include both `client_type=osc` and `client_id` parameter
- [ ] Implement OSC server component (UDP listener)
- [ ] Implement OSC client component (UDP sender)

### Phase 2: Message Translation
- [ ] Create YAML configuration parser
- [ ] Implement WebSocket → OSC message translation
  - Field mapping from WebSocket JSON to OSC arguments
  - Type conversion (bool→int, etc.)
  - Multiple destinations per WebSocket event
- [ ] Implement OSC → WebSocket message translation
  - OSC argument extraction
  - Field mapping to WebSocket JSON
  - Type validation

### Phase 3: Configuration & Error Handling
- [ ] Add configuration file support (YAML)
- [ ] Add logging (DEBUG, INFO, WARN levels)
- [ ] Add error handling for:
  - Network errors (WebSocket disconnect, OSC send failures)
  - Invalid OSC messages
  - Configuration errors
  - Type conversion errors
- [ ] Add reconnection logic for WebSocket (copy from `/hardware/buzzers.py`)

### Phase 4: Testing & Documentation
- [ ] Test with OSC testing tools:
  - `oscsend`/`oscdump` (command-line tools)
  - TouchOSC (mobile app)
  - Pure Data or Max/MSP (if available)
- [ ] Create example configurations:
  - Basic buzzer control
  - Lighting integration (QLab-style)
  - MIDI controller mapping
- [ ] Create README documentation:
  - Installation instructions
  - Configuration guide
  - OSC message reference
  - Troubleshooting guide
- [ ] Add systemd service file for auto-start (optional)

## OSC Library: python-osc (pythonosc)

**Decision: Use `python-osc`** ✅

### Key Details

**Note:** `python-osc` and `pythonosc` are **the same library**:
- **Install:** `pip install python-osc` (PyPI package name)
- **Import:** `from pythonosc import ...` (module name)

### Why python-osc?

**Active Maintenance:**
- Latest release: **Dec 23, 2024** (v1.9.3)
- GitHub: [attwad/python-osc](https://github.com/attwad/python-osc)
- Rated "Sustainable" by [Snyk](https://snyk.io/advisor/python/python-osc)
- 550+ stars, 8,000+ weekly downloads

**Perfect for This Use Case:**
- **Asyncio support** - Critical for integration with async WebSocket client
- Pure Python, **zero dependencies**
- Requires Python >=3.10 (matches project requirements)
- OSC 1.0 spec compliant
- UDP and TCP support (UDP for OSC)

**Production Ready:**
- Status: 5 - Production/Stable
- Comprehensive unit tests
- Good [documentation](https://python-osc.readthedocs.io/)

### Alternative Considered

**oscpy** (by Kivy team) - Not chosen because:
- Last updated June 2021 (4+ years old)
- Still in beta status
- Only relevant for Python 2.7 support (not needed)

## Example Use Cases

### Use Case 1: OSC-Based Buzzer System
Replace GPIO buzzers with wireless OSC controllers (tablets, phones, MIDI controllers):
```yaml
incoming:
  - osc_address: "/buzzer/1"
    websocket_type: "buzzer_pressed"
    args:
      - osc_index: 0
        websocket_field: "buzzerId"
        type: "int"
```

### Use Case 2: Lighting Control (QLab Integration)
Trigger lighting cues when questions are selected:
```yaml
outgoing:
  - websocket_type: "select_question"
    osc_destinations:
      - host: "192.168.1.10"
        port: 53000
        address: "/cue/selected/start"
        args:
          - field: "question"
            type: "int"
```

### Use Case 3: Sound Effects
Play sound effects when buzzers are enabled/disabled:
```yaml
outgoing:
  - websocket_type: "toggle_buzzers"
    osc_destinations:
      - host: "192.168.1.20"
        port: 9000
        address: "/sound/play"
        args:
          - field: "enabled"
            type: "int"  # 1=enable sound, 0=disable sound
```

## Dependencies

- **TODO #24** (Hardware WebSocket Client Library) - Should be implemented first for reusable WebSocket connection logic
- **python-osc** (v1.9.3+) - `pip install python-osc`
- **PyYAML** - `pip install pyyaml` (for configuration parsing)
- **websockets** library (already used by `/hardware/buzzers.py`)
- Python >=3.10
- No backend changes required

## Priority

**Medium** - Enables professional A/V integration, expands hardware options beyond GPIO.

Should be implemented **after TODO #24** (Hardware WebSocket Client Library) for code reuse.

## Related TODOs

- **TODO #24** (Hardware WebSocket Client Library) - Prerequisite: provides base class for WebSocket clients
- **TODO #23** (Connection Status Overlay) - Will benefit from this bridge's connection tracking
- References `/hardware/buzzers.py` as implementation pattern
- Could integrate with TODO #18 (REST Endpoints) for hybrid control
- Independent of authentication TODOs (uses same WebSocket pattern as existing hardware)

## Notes

- Bridge runs as separate process, not part of Django application
- Multiple bridge instances can run simultaneously (different `client_id` values)
- Configuration is per-bridge-instance (multiple configs for different setups)
- No database persistence required (pure message translation)
- Follows existing hardware client pattern (similar to `/hardware/buzzers.py`)
