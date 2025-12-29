# Account-Based Authentication for Human Users

## Problem

Currently, the application has no authentication mechanism. All HTTP API endpoints and WebSocket connections are publicly accessible, relying solely on network boundary security. This is insufficient for:
- Multi-tenant deployments
- Controlled access to specific games
- Audit trails and accountability
- Protecting sensitive game data

## Proposed Solution

Implement cookie/session-based authentication for human users with Django's built-in authentication system.

### Key Features

1. **User Accounts**
   - Use Django's built-in `User` model (username, email, password)
   - Standard login/logout endpoints
   - Session-based authentication via cookies

2. **Many-to-Many Game Access**
   - `GameAccess` model linking Users to Games
   - Users can have access to multiple games
   - Games can be accessed by multiple users
   - No role-based permissions beyond game-level access (no admin/viewer distinction)

3. **Authentication Requirements**
   - All existing API endpoints require authentication
   - WebSocket connections require authentication
   - Unauthenticated requests return 401 Unauthorized

## Data Model

```python
# Built-in Django User model (no changes needed)
User:
  - id
  - username
  - email
  - password (hashed)
  - date_joined

# New model for game access control
GameAccess:
  - id
  - user: ForeignKey(User)
  - game: ForeignKey(Game)
  - granted_at: DateTimeField
  - granted_by: ForeignKey(User, null=True)  # Who granted access

  class Meta:
    unique_together = [['user', 'game']]
```

## API Endpoints

### Authentication Endpoints
- `POST /api/auth/login/` - Login with username/password, returns session cookie
- `POST /api/auth/logout/` - Logout and invalidate session
- `GET /api/auth/me/` - Get current user info

### Game Access Management (Future - not in initial scope)
- `GET /api/games/` - List games user has access to
- `POST /api/games/{game_id}/access/` - Grant user access to game (admin only)
- `DELETE /api/games/{game_id}/access/{user_id}/` - Revoke access (admin only)

## Implementation Steps

### High Priority
- [ ] Enable Django authentication system in settings
- [ ] Create `GameAccess` model with User-Game many-to-many relationship
- [ ] Create authentication endpoints (login, logout, me)
- [ ] Add authentication middleware to all existing API endpoints
- [ ] Add permission check: user must have GameAccess for requested game
- [ ] Update WebSocket consumer to require authentication
- [ ] Add migration for GameAccess model

### Medium Priority
- [ ] Create management command to create initial users and grant access
- [ ] Add password reset functionality (email-based)
- [ ] Update frontend to handle login/logout flow
- [ ] Handle 401 responses in frontend API client

### Testing
- [ ] Unit tests for GameAccess model
- [ ] Integration tests for authentication endpoints
- [ ] Tests for permission enforcement on existing endpoints
- [ ] Tests for WebSocket authentication

### Documentation
- [ ] Update API documentation with authentication requirements
- [ ] Document how to create users and grant game access
- [ ] Update README with authentication setup instructions

## Security Considerations

- Use Django's built-in password hashing (PBKDF2 by default)
- Enable CSRF protection for cookie-based auth (already enabled)
- Set secure cookie flags in production (Secure, HttpOnly, SameSite)
- Consider session timeout settings
- Update CORS settings to be more restrictive (remove ALLOW_ALL)

## Authorization Logic

For each API request:
1. Check if user is authenticated (Django session middleware)
2. Extract `game_id` from request (URL param, body, or related object)
3. Verify `GameAccess.objects.filter(user=request.user, game=game).exists()`
4. Return 403 Forbidden if no access, continue if access granted

## Dependencies

- Django built-in auth (already installed)
- No additional packages required for basic implementation

## Priority

**High** - Foundation for security model, blocks API key auth and external integrations.

## Related TODOs

- TODO #17: API Key Authentication (depends on this)
- TODO #18: REST Endpoints for External Control (requires authentication)
