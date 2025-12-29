# API Key Authentication for Machine Clients

## Problem

Machine clients (CLI tools, hardware controllers, automation scripts) cannot use cookie-based session authentication effectively because:
- No browser to store/send cookies
- Long-running processes need persistent credentials
- Hardware devices need simple token-based auth
- Automated systems can't perform interactive login

## Proposed Solution

Implement API key authentication for machine clients using token-based authentication with the same game-level access control as human accounts.

### Key Features

1. **API Keys**
   - Long-lived tokens for machine authentication
   - Human-readable key format (e.g., `qz_dev_1a2b3c4d5e6f...`)
   - Securely hashed in database (like passwords)
   - Can be revoked individually

2. **Many-to-Many Game Access**
   - `APIKeyGameAccess` model linking API Keys to Games
   - One API key can access multiple games
   - One game can be accessed by multiple API keys
   - No role-based permissions beyond game-level access

3. **Authentication Method**
   - Header-based: `Authorization: Bearer <api_key>`
   - Validates on every request
   - Stateless (no sessions)

## Data Model

```python
APIKey:
  - id
  - name: CharField  # Human-readable identifier (e.g., "Buzzer Controller 1")
  - key_prefix: CharField  # First 8 chars for display (e.g., "qz_dev_1")
  - key_hash: CharField  # Hashed full key (bcrypt/scrypt)
  - created_at: DateTimeField
  - created_by: ForeignKey(User)  # Human who created this key
  - last_used_at: DateTimeField(null=True)
  - is_active: BooleanField  # For soft-delete/revocation

APIKeyGameAccess:
  - id
  - api_key: ForeignKey(APIKey)
  - game: ForeignKey(Game)
  - granted_at: DateTimeField

  class Meta:
    unique_together = [['api_key', 'game']]
```

## API Key Format

```
qz_{environment}_{random_string}

Examples:
- qz_dev_a8f4c2e9b3d1f6a2c8e4b9d3f1a6c2e8
- qz_prod_3c1e8a4f2d9b6c3e1a8f4d2b9c6e3a1f

Components:
- "qz_" prefix (identifies as quizzer API key)
- environment (dev/prod/test) for safety
- 32 character random hex string
```

## API Endpoints

### API Key Management
- `POST /api/api-keys/` - Create new API key (returns full key once)
  - Body: `{name, game_ids: [...]}`
  - Response: `{id, name, key, key_prefix, created_at}`
  - ⚠️ Full key shown only on creation, never retrievable again

- `GET /api/api-keys/` - List user's API keys (shows prefix only)
  - Response: `[{id, name, key_prefix, created_at, last_used_at, is_active}]`

- `DELETE /api/api-keys/{id}/` - Revoke API key
  - Sets `is_active = False`

- `POST /api/api-keys/{id}/grant-access/` - Grant game access
  - Body: `{game_id}`

- `DELETE /api/api-keys/{id}/revoke-access/{game_id}/` - Revoke game access

### Using API Keys
All existing endpoints accept:
```
Authorization: Bearer qz_dev_a8f4c2e9b3d1f6a2c8e4b9d3f1a6c2e8
```

## Implementation Steps

### High Priority
- [ ] Create `APIKey` and `APIKeyGameAccess` models
- [ ] Implement API key generation with secure random bytes
- [ ] Implement API key hashing (use Django's `make_password`)
- [ ] Create custom authentication backend for API keys
- [ ] Add `APIKeyAuthentication` class for DRF
- [ ] Update view permission checks to handle both User and APIKey auth
- [ ] Create API key management endpoints
- [ ] Add migrations

### Medium Priority
- [ ] Implement `last_used_at` tracking (update on each request)
- [ ] Add API key prefix indexing for faster lookups
- [ ] Create management command to generate API keys from CLI
- [ ] Add rate limiting per API key (optional)

### Testing
- [ ] Unit tests for API key generation and hashing
- [ ] Integration tests for API key authentication
- [ ] Tests for game access permission checks
- [ ] Tests for key revocation
- [ ] Security tests (invalid keys, revoked keys, expired keys)

### Documentation
- [ ] Document API key creation process
- [ ] Document API key usage in requests
- [ ] Add examples for CLI and hardware clients
- [ ] Security best practices for key storage

## Authentication Flow

```python
# In custom authentication backend
def authenticate_api_key(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    key = auth_header[7:]  # Remove "Bearer "

    # Extract prefix for fast lookup
    prefix = key[:11]  # "qz_dev_xxx"

    # Find potential keys by prefix
    api_keys = APIKey.objects.filter(
        key_prefix=prefix,
        is_active=True
    )

    # Check each key's hash
    for api_key in api_keys:
        if check_password(key, api_key.key_hash):
            # Update last used timestamp (async?)
            api_key.last_used_at = timezone.now()
            api_key.save(update_fields=['last_used_at'])
            return api_key

    return None
```

## Authorization Logic

Same as user authentication, but checks `APIKeyGameAccess` instead of `GameAccess`:

```python
def has_game_access(request, game):
    if isinstance(request.auth, User):
        return GameAccess.objects.filter(
            user=request.auth, game=game
        ).exists()
    elif isinstance(request.auth, APIKey):
        return APIKeyGameAccess.objects.filter(
            api_key=request.auth, game=game
        ).exists()
    return False
```

## Security Considerations

- API keys hashed with `make_password()` (PBKDF2)
- Full key displayed only once at creation
- Store keys securely on client side (environment variables, config files)
- Support key rotation (create new, delete old)
- No key expiration in initial implementation (can add later)
- Rate limiting to prevent brute force (optional)

## CLI Integration Example

```bash
# Set API key in environment
export QUIZZER_API_KEY="qz_dev_a8f4c2e9b3d1f6a2c8e4b9d3f1a6c2e8"

# CLI tool uses it automatically
quizzer-cli game 123 buzzers enable

# Or pass directly
quizzer-cli --api-key "qz_dev_..." game 123 buzzers enable
```

## Hardware Integration Example

```python
# In hardware controller config
[auth]
api_key = qz_prod_3c1e8a4f2d9b6c3e1a8f4d2b9c6e3a1f

# In hardware controller code
headers = {
    'Authorization': f'Bearer {config.api_key}',
    'Content-Type': 'application/json'
}
response = requests.post(
    f'{base_url}/api/game/{game_id}/buzzers/state',
    headers=headers,
    json={'enabled': True}
)
```

## Dependencies

- Django built-in password hashing (already available)
- No additional packages required

## Priority

**High** - Required for CLI client and hardware integration use cases.

## Related TODOs

- TODO #16: Account-Based Authentication (prerequisite)
- TODO #18: REST Endpoints for External Control (will use API key auth)
