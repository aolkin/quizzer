# Quizzer - Interactive Jeopardy Game System

A modern, multi-client Jeopardy game application with real-time synchronization,
host mode, and support for custom hardware buzzers. Built with SvelteKit
frontend and Django backend.

Also an experiment in AI-assisted coding, portions of the repository were
bootstrapped or improved with the use of AI assistants (including this README).

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
# On Raspberry Pi:
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
```

## Hardware Buzzer Wiring

For Raspberry Pi GPIO setup:

```
GPIO 23, 24, 25 → Multiplexer select pins (S0, S1, S2)
GPIO 16 → Enable pin (EN)
GPIO 18 → Input pin (SIG)
```

Connect up to 8 buzzers through a 74HC4051 multiplexer.

TODO: Add more details on the wiring and hardware setup.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

