# Game Import/Export

## Problem

Currently, there's no way to:
- **Backup game data** for archival or disaster recovery
- **Share game templates** between instances or users
- **Duplicate games** with different teams/players
- **Migrate games** between environments (dev/staging/prod)
- **Create game templates** for reuse (e.g., standard Jeopardy board formats)
- **Version control game content** outside the database

Users must manually recreate game boards, categories, and questions, which is time-consuming and error-prone.

## Use Cases

1. **Game Templates**: Export a board structure (categories, questions) without team/player data for reuse
2. **Full Backup**: Export complete game state including teams, players, and answers for archival
3. **Content Sharing**: Share interesting game boards with other quizzer instances
4. **Migration**: Move games between development and production environments
5. **Version Control**: Store game content in git alongside code
6. **Bulk Creation**: Create games programmatically from structured data files

## Proposed Solution

Add REST API endpoints for exporting and importing game data in JSON format.

### Export Endpoint

```
GET /api/game/{game_id}/export?mode=template|full
```

**Modes:**
- `template` (default): Exports game structure only (boards, categories, questions) - no teams, players, or answers
- `full`: Exports complete game state including teams, players, and answer history

**Response:**
```json
{
  "export_version": "1.0",
  "mode": "template",
  "exported_at": "2025-12-29T10:30:00Z",
  "game": {
    "name": "Science Jeopardy",
    "mode": "jeopardy",
    "boards": [
      {
        "name": "Round 1",
        "order": 0,
        "categories": [
          {
            "name": "Physics",
            "order": 0,
            "questions": [
              {
                "text": "What is the speed of light?",
                "answer": "299,792,458 m/s",
                "points": 100,
                "type": "text",
                "media_url": null
              }
            ]
          }
        ]
      }
    ],
    "teams": [],  // Empty in template mode
    "metadata": {
      "original_game_id": 123,
      "created_at": "2025-12-20T10:00:00Z"
    }
  }
}
```

### Import Endpoint

```
POST /api/game/import
```

**Request Body:** Same format as export response

**Response:**
```json
{
  "game_id": 456,
  "game_name": "Science Jeopardy",
  "boards_created": 2,
  "categories_created": 10,
  "questions_created": 50,
  "teams_created": 0,
  "import_mode": "template"
}
```

**Behavior:**
- Creates a new game (never updates existing)
- Validates JSON structure before import
- Atomic transaction (all-or-nothing)
- Returns detailed summary of created objects

## Export Modes

### Template Mode (Default)
**Exports:**
- ✅ Game name and mode
- ✅ Boards (name, order)
- ✅ Categories (name, order)
- ✅ Questions (text, answer, points, type, media_url)
- ✅ Metadata (original game ID, creation date)

**Excludes:**
- ❌ Teams and players
- ❌ Answer history
- ❌ Question answered state
- ❌ Player scores
- ❌ Database IDs (regenerated on import)

**Use case:** Sharing reusable game content

### Full Mode
**Exports everything in template mode plus:**
- ✅ Teams (name, color)
- ✅ Players (name, buzzer, team association)
- ✅ Answer history (who answered what, when, correct/incorrect)
- ✅ Question answered state
- ✅ Player scores (current totals)

**Excludes:**
- ❌ Database IDs (regenerated on import)
- ❌ Created/updated timestamps (regenerated)
- ❌ WebSocket connection state

**Use case:** Complete backup/restore

## API Specification

### Export Endpoint

**URL:** `GET /api/game/{game_id}/export`

**Query Parameters:**
- `mode`: `template` or `full` (default: `template`)
- `pretty`: `true` or `false` (default: `false`) - for human-readable JSON

**Authentication:** Required (cookie or API key)

**Authorization:** User/API key must have access to the game

**Response:** JSON export file (content-type: `application/json`)

**Response Headers:**
- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="game-{game_id}-{timestamp}.json"`

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - No access to this game
- `404 Not Found` - Game does not exist

### Import Endpoint

**URL:** `POST /api/game/import`

**Request Body:** JSON export file (same format as export response)

**Authentication:** Required (cookie or API key)

**Authorization:** Authenticated user (game access granted automatically to importer)

**Response (201 Created):**
```json
{
  "game_id": integer,
  "game_name": string,
  "boards_created": integer,
  "categories_created": integer,
  "questions_created": integer,
  "teams_created": integer,
  "players_created": integer,
  "answers_imported": integer,
  "import_mode": "template" | "full",
  "imported_at": "ISO 8601 timestamp"
}
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `400 Bad Request` - Invalid JSON structure or validation errors
- `422 Unprocessable Entity` - Valid JSON but semantic errors (e.g., duplicate categories)

**Validation:**
- Export version compatibility check
- Required fields present
- Data type validation
- Referential integrity (e.g., questions reference valid categories)

## Implementation Steps

### High Priority
- [ ] Create export serializers (template and full modes)
- [ ] Create `GET /api/game/{game_id}/export` endpoint
- [ ] Add mode parameter handling (template vs full)
- [ ] Implement JSON export with proper nesting (boards → categories → questions)
- [ ] Create import serializer with validation
- [ ] Create `POST /api/game/import` endpoint
- [ ] Implement atomic import transaction
- [ ] Add authentication and authorization checks
- [ ] Auto-grant game access to importer

### Medium Priority
- [ ] Add `pretty` parameter for human-readable exports
- [ ] Generate filename with timestamp in Content-Disposition header
- [ ] Add export version checking for compatibility
- [ ] Add detailed import validation errors
- [ ] Support importing answer history in full mode
- [ ] Add dry-run option for import validation without creation

### Testing
- [ ] Integration tests for export endpoint (template and full modes)
- [ ] Integration tests for import endpoint
- [ ] Tests for round-trip (export → import → export should match)
- [ ] Tests for validation errors (malformed JSON, missing fields)
- [ ] Tests for authentication/authorization
- [ ] Tests for transaction rollback on import errors

### Documentation
- [ ] API endpoint documentation for export and import
- [ ] Export JSON schema documentation
- [ ] Example export files (template and full)
- [ ] CLI usage examples (curl, wget)
- [ ] Game template library examples

## JSON Schema (Template Mode)

```json
{
  "type": "object",
  "required": ["export_version", "mode", "game"],
  "properties": {
    "export_version": {"type": "string", "enum": ["1.0"]},
    "mode": {"type": "string", "enum": ["template", "full"]},
    "exported_at": {"type": "string", "format": "date-time"},
    "game": {
      "type": "object",
      "required": ["name", "mode", "boards"],
      "properties": {
        "name": {"type": "string"},
        "mode": {"type": "string", "enum": ["jeopardy"]},
        "boards": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "order", "categories"],
            "properties": {
              "name": {"type": "string"},
              "order": {"type": "integer"},
              "categories": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["name", "order", "questions"],
                  "properties": {
                    "name": {"type": "string"},
                    "order": {"type": "integer"},
                    "questions": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "required": ["text", "answer", "points"],
                        "properties": {
                          "text": {"type": "string"},
                          "answer": {"type": "string"},
                          "points": {"type": "integer"},
                          "type": {"type": "string", "enum": ["text", "image", "video", "audio"]},
                          "media_url": {"type": ["string", "null"]}
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "teams": {"type": "array"},
        "metadata": {
          "type": "object",
          "properties": {
            "original_game_id": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"}
          }
        }
      }
    }
  }
}
```

## Future Enhancements (Not in Initial Scope)

### Import Options
- `POST /api/game/import?mode=merge` - Merge with existing game instead of creating new
- `POST /api/game/import?validate_only=true` - Dry-run validation without import
- Support for partial imports (boards only, questions only, etc.)

### Export Options
- `GET /api/game/{game_id}/export?format=csv` - CSV format for spreadsheet editing
- `GET /api/board/{board_id}/export` - Export single board instead of full game
- Bulk export: `GET /api/games/export?ids=1,2,3`

### Template Library
- Public template repository (if multi-tenant)
- Template sharing between users
- Template ratings and reviews
- Searchable template catalog

## Integration Examples

### Export via curl
```bash
# Export template
curl -H "Authorization: Bearer ${API_KEY}" \
  "http://localhost:8000/api/game/123/export?mode=template&pretty=true" \
  -o game-template.json

# Export full backup
curl -H "Authorization: Bearer ${API_KEY}" \
  "http://localhost:8000/api/game/123/export?mode=full" \
  -o game-backup-$(date +%Y%m%d).json
```

### Import via curl
```bash
# Import game template
curl -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @game-template.json \
  http://localhost:8000/api/game/import

# Validate before importing
curl -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @game-template.json \
  "http://localhost:8000/api/game/import?validate_only=true"
```

### CLI Integration
```bash
# Export
quizzer-cli game 123 export --mode template -o my-game.json

# Import
quizzer-cli game import my-game.json

# Round-trip test
quizzer-cli game 123 export -o original.json
quizzer-cli game import original.json
quizzer-cli game 456 export -o copy.json
diff original.json copy.json  # Should match (except IDs, timestamps)
```

## Security Considerations

- **Authentication required** for both import and export
- **Game access required** for export (prevent data leakage)
- **Auto-grant access** to importer (they created the game)
- **Size limits** on import JSON (prevent DoS via huge files)
- **Validation** to prevent injection attacks via malicious JSON
- **No sensitive data** exported (passwords, API keys, etc.)

## Dependencies

- Django REST Framework (already installed)
- No new packages required
- Depends on TODO #16 (Account Authentication)
- Depends on TODO #17 (API Key Authentication)

## Priority

**Medium** - Nice to have for game management, but not blocking core functionality.

## Related TODOs

- TODO #16: Account-Based Authentication (prerequisite)
- TODO #17: API Key Authentication (prerequisite)
