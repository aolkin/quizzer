# Quizzer - Interactive Jeopardy Game System

[![Backend CI](https://github.com/aolkin/quizzer/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/aolkin/quizzer/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/aolkin/quizzer/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/aolkin/quizzer/actions/workflows/frontend-ci.yml)

A modern, multi-client Jeopardy game application with real-time synchronization,
host mode, and support for custom hardware buzzers. Built with SvelteKit
frontend and Django backend.

## Features

### 🎯 Core Game Features
- **Classic Jeopardy gameplay** with customizable boards and categories
- **Multi-media questions** supporting text, images, videos, and audio
- **Special questions** and Daily Double support
- **Real-time scoring** with team and individual player tracking
- **Question state management** (answered/unanswered tracking)

### 🌐 Multi-Client Architecture
- **Real-time synchronization** across all connected clients using WebSockets
- **Host mode** for game administration and control
- **Player clients** for team participation
- **Spectator mode** for viewing without participation
- **Cross-platform compatibility** - works on any device with a web browser

### 🔧 Hardware Integration
- **Custom buzzer support** via Raspberry Pi GPIO
- **Buzzer system** supporting up to 8 buzzers using a hardware multiplexer
- **Real-time buzzer detection** with hardware debouncing
- **Buzzer LEDs** via a second multiplexer
- **Automatic reconnection** and fault tolerance

### 🎨 Modern UI/UX
- **Responsive design** built with TailwindCSS and Skeleton UI
- **Real-time audio feedback** with configurable sound effects
- **Color-coded teams** for easy identification
- **Smooth animations** and transitions

## Architecture

### Frontend (`/app`)
- **Framework**: SvelteKit with TypeScript
- **Styling**: TailwindCSS + Skeleton UI components
- **State Management**: Svelte stores with reactive updates
- **Real-time Communication**: WebSocket integration
- **Audio System**: Built-in sound effects and feedback

### Backend (`/service`)
- **Framework**: Django with Django REST Framework
- **Real-time**: Django Channels with WebSocket support
- **Database**: SQLite (configurable for PostgreSQL/MySQL)
- **API**: RESTful endpoints for game management
- **Admin Interface**: Django admin for content management

### Hardware (`/hardware`)
- **Platform**: Raspberry Pi with GPIO control
- **Buzzer System**: Custom multiplexed buzzer controller
- **Communication**: WebSocket client for real-time integration

## Communication Architecture

The system uses a **hybrid REST + WebSocket architecture** optimized for real-time game synchronization:

### WebSocket Broadcast Relay Pattern
For **ephemeral UI coordination** (game state that doesn't persist):
- Client sends coordination message (e.g., `{type: 'select_question', question: 5}`)
- Server **forwards message as-is** to all connected clients (relay/broadcast)
- No server-side processing or validation - just routing
- Examples: `select_question`, `reveal_category`, `select_board`

**Why this pattern:**
- Fast iteration - add new UI features without server changes
- Minimal latency - no processing overhead
- Simple mental model - client-to-client coordination via server relay
- Perfect for trusted environments (local game night)

### REST API for Persistence
For **database mutations** (scores, question state):
- Client sends HTTP request to REST endpoint
- Server validates, updates database, returns response with version number
- Server broadcasts update to all WebSocket clients
- All clients (including requester) update UI from broadcast
- Version numbers prevent race conditions from out-of-order messages

**Why this pattern:**
- Proper error handling (HTTP status codes)
- Immediate feedback to requester
- Prevents stuck states (always get response)
- Built-in retry mechanisms
- Easy to test

### Message Flow Example
```
Host selects question (coordination):
  Client → WS: {type: 'select_question', question: 5}
  Server → All clients via WS: (same message)
  All UIs update

Host awards points (persistence):
  Client → REST: POST /api/games/1/answers/ {playerId: 1, isCorrect: true}
  Server → Client: 200 OK {score: 600, version: 42}
  Server → All clients via WS: {type: 'update_score', playerId: 1, score: 600, version: 42}
  All UIs update (using version to ignore stale updates)
```

This hybrid approach combines the simplicity of broadcast relay with the robustness of REST APIs.

## Quick Start

### Prerequisites
- Node.js 18+ and Bun (for frontend)
- Python 3.9+ (for backend)
- Raspberry Pi with GPIO (for hardware buzzers, optional)

### Backend Setup
```bash
cd service
# Install python packages
# TODO: Actually create a requirements.txt
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd app
bun install
bun run dev
```

### Hardware Buzzers (Optional)
```bash
cd hardware
pip install -r requirements.txt
# On Raspberry Pi:
python buzzers.py <game_id>

# With custom server:
python buzzers.py <game_id> --server myserver.local:8000

# With custom log level:
python buzzers.py <game_id> --log-level DEBUG

# Using environment variables:
export QUIZZER_SERVER=myserver.local:8000
export QUIZZER_LOG_LEVEL=DEBUG
python buzzers.py <game_id>
```

## Game Setup

1. **Create a Game**: Use Django admin at `http://localhost:8000/admin/`
2. **Add Boards**: Create one or more game boards
3. **Add Categories**: Set up categories for each board
4. **Add Questions**: Create questions with points, answers, and optional media
5. **Create Teams**: Set up teams with custom colors
6. **Add Players**: Assign players to teams with optional buzzer numbers

## API Endpoints

### Games
- `GET /api/games/` - List all games
- `POST /api/games/` - Create new game
- `GET /api/games/{id}/` - Get game details

### Teams & Players
- `GET /api/games/{game_id}/teams/` - List teams for game
- `POST /api/games/{game_id}/teams/` - Create team
- `POST /api/teams/{team_id}/players/` - Add player to team

### WebSocket Events
Connect to: `ws://localhost:8000/ws/game/{game_id}/`

#### Client → Server
```json
{
  "type": "toggle_buzzers",
  "enabled": true
}

{
  "type": "buzzer_pressed", 
  "buzzerId": 3
}

{
  "type": "answer_question",
  "questionId": 123,
  "playerId": 456,
  "isCorrect": true,
  "points": 400
}
```

#### Server → Client
```json
{
  "type": "game_state_update",
  "board": {...},
  "teams": [...],
  "currentQuestion": {...}
}

{
  "type": "buzzer_pressed",
  "buzzerId": 3,
  "playerId": 456
}
```

## Development

### Prerequisites for Development
- Python 3.12+ (for backend)
- Bun (for frontend)
- (Optional) pre-commit for automated code quality checks

### Setting Up Pre-commit Hooks

For the best development experience, install pre-commit hooks to automatically check code quality before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

The pre-commit hooks will automatically:
- Format Python code with Black (configured in `service/pyproject.toml`)
- Lint Python code with Flake8 (configured in `service/.flake8`)
- Format JavaScript/TypeScript/Svelte with Prettier
- Check for trailing whitespace and other common issues

### Frontend Development
```bash
cd app
bun run dev          # Start dev server
bun run build        # Build for production
bun run preview      # Preview production build
bun run check        # Type checking
bun run lint         # Lint and format
bun run test         # Run tests
```

### Backend Development
```bash
cd service
python manage.py runserver    # Start dev server
python manage.py shell        # Django shell
python manage.py test         # Run tests
black .                       # Format code
flake8 .                      # Lint code
```

### Running Quality Checks Locally

Before submitting a PR, ensure all checks pass:

```bash
# Backend checks
cd service
black --check .
flake8 .
python manage.py test

# Frontend checks
cd app
bun run lint
bun run check
bun run test
bun run build
```

Configuration for linters and formatters:
- **Backend**: Black configured in `service/pyproject.toml` (line length: 100), Flake8 configured in `service/.flake8` (max line length: 100, ignores: E203, W503)
- **Frontend**: JavaScript/TypeScript style configured via ESLint and Prettier configs in `app/`

### Testing

See [TESTING.md](TESTING.md) for our testing philosophy and guidelines. Key principles:
- Focus on **high-value tests** that verify complex logic and prevent regressions
- Avoid trivial tests for simple setters/getters or framework behavior
- Test behavior, not implementation
- Mock external dependencies

## Hardware Buzzer Wiring

The hardware buzzer system uses a Raspberry Pi with GPIO to support up to 8 buzzers through a 74HC4051 8-channel analog multiplexer.

### Components Required
- Raspberry Pi (any model with GPIO pins)
- 74HC4051 8-channel analog multiplexer IC
- 8 momentary push buttons (buzzers)
- Pull-down resistors (10kΩ recommended for each buzzer)
- Jumper wires
- Breadboard (for prototyping) or custom PCB

### Pin Connections

#### Raspberry Pi GPIO to 74HC4051
```
Raspberry Pi GPIO → 74HC4051 Pin
─────────────────────────────────
GPIO 23 (Pin 16)  → S0 (Pin 11) - Select bit 0
GPIO 24 (Pin 18)  → S1 (Pin 10) - Select bit 1  
GPIO 25 (Pin 22)  → S2 (Pin 9)  - Select bit 2
GPIO 16 (Pin 36)  → INH (Pin 6) - Enable/Inhibit (active low)
GPIO 18 (Pin 12)  → Z (Pin 3)   - Signal input/output
3.3V             → VCC (Pin 16) - Power supply
GND              → VEE (Pin 8)  - Ground
GND              → GND (Pin 7)  - Ground
```

#### 74HC4051 to Buzzers
```
74HC4051 Pin → Buzzer Connection
────────────────────────────────
Y0 (Pin 13)  → Buzzer 0 (one side)
Y1 (Pin 14)  → Buzzer 1 (one side)
Y2 (Pin 15)  → Buzzer 2 (one side)
Y3 (Pin 12)  → Buzzer 3 (not used - reserved)
Y4 (Pin 1)   → Buzzer 4 (one side)
Y5 (Pin 5)   → Buzzer 5 (one side)
Y6 (Pin 2)   → Buzzer 6 (one side)
Y7 (Pin 4)   → Buzzer 7 (one side)

Note: Buzzer 3 is skipped in the code (see line 62-63 in buzzers.py)
```

#### Buzzer Wiring
Each buzzer should be wired as follows:
```
[3.3V] ──┬── [Buzzer Button] ──┬── [10kΩ Resistor] ── [GND]
         │                      │
         └──────────────────────┴── [74HC4051 Yx pin]
```

When a buzzer is pressed, it connects the multiplexer channel to 3.3V. The pull-down resistor ensures a clean LOW signal when not pressed.

### Software Configuration

#### Basic Usage
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default server (quasar.local:8000)
python buzzers.py 1

# Run with custom server
python buzzers.py 1 --server 192.168.1.100:8000

# Run with debug logging
python buzzers.py 1 --log-level DEBUG
```

#### Environment Variables
- `QUIZZER_SERVER`: Server URL (default: `quasar.local:8000`)
- `QUIZZER_LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: `INFO`)

#### Features
- **Automatic reconnection**: If the WebSocket connection drops, the script automatically attempts to reconnect
- **Health monitoring**: Built-in ping/pong heartbeat (15s interval, 5s timeout) to detect stale connections
- **Graceful shutdown**: Handles SIGTERM and SIGINT signals to properly cleanup GPIO pins
- **Buzzer safety**: Buzzers are automatically disabled when connection is lost to prevent phantom presses

### Troubleshooting

**Buzzers not responding:**
- Check that all GPIO connections are secure
- Verify 74HC4051 is receiving 3.3V power
- Test individual buzzers with a multimeter
- Run with `--log-level DEBUG` to see detailed connection info

**Connection issues:**
- Verify the server URL is correct
- Check network connectivity to the server
- Ensure the game ID exists in the database
- Check firewall settings allow WebSocket connections on port 8000

**GPIO cleanup errors:**
- The script automatically cleans up GPIO on exit
- If pins are left in a bad state, run: `python -c "import RPi.GPIO as gpio; gpio.setmode(gpio.BCM); gpio.cleanup()"`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

