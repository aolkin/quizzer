# API Key Authentication for Machine Clients

## Problem

Machine clients (CLI tools, hardware controllers, automation scripts) cannot use cookie-based session authentication effectively because:
- No browser to store/send cookies
- Long-running processes need persistent credentials
- Hardware devices need simple token-based auth
- Automated systems can't perform interactive login

## Proposed Solution

Implement API key authentication for machine clients using token-based authentication with the same game-level access control as human accounts.

### Recommended Library

Use **`djangorestframework-api-key`** - a well-maintained library for API key management:
- Provides `APIKey` model with secure hashing
- Includes DRF authentication class
- Built-in admin interface
- Supports key prefixes and revocation
- PyPI: `pip install djangorestframework-api-key`

**Alternative consideration**: Custom implementation using Django's built-in auth, but the library provides battle-tested security and convenience.

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

### From `djangorestframework-api-key` library:
```python
APIKey:  # Provided by the library
  - id
  - prefix: CharField  # e.g., "qz_dev_ab"
  - hashed_key: CharField  # Securely hashed
  - created: DateTimeField
  - name: CharField  # Human-readable identifier
  - revoked: BooleanField  # For revocation
```

### Custom model for game access:
```python
APIKeyGameAccess:
  - id
  - api_key: ForeignKey(APIKey)  # From library
  - game: ForeignKey(Game)
  - granted_at: DateTimeField
  - granted_by: ForeignKey(User, null=True)  # Who granted access

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

## API Key Management

API keys will be managed through **Django Admin** interface:
- Create new API keys (full key displayed once)
- List existing keys (prefix only)
- Revoke keys (soft delete via `is_active` flag)
- Grant/revoke game access via inline forms

### Using API Keys
All existing endpoints accept:
```
Authorization: Bearer qz_dev_a8f4c2e9b3d1f6a2c8e4b9d3f1a6c2e8
```

## Implementation Steps

### High Priority
- [ ] Install `djangorestframework-api-key` package
- [ ] Create `APIKeyGameAccess` model for many-to-many game access
- [ ] Configure Django admin for API key management
  - [ ] Register `APIKey` model (from library) with custom admin
  - [ ] Add inline for `APIKeyGameAccess` in admin
  - [ ] Display full key only on creation (customize save method)
- [ ] Add `APIKeyAuthentication` to DRF authentication classes
- [ ] Update view permission checks to handle both User and APIKey auth
- [ ] Add migrations for `APIKeyGameAccess`

### Medium Priority
- [ ] Customize API key prefix format (e.g., "qz_dev_", "qz_prod_")
- [ ] Add helpful text in admin for key management
- [ ] Document Django admin workflow for creating keys
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

The `djangorestframework-api-key` library provides `APIKeyAuthentication` class that handles:
1. Extracting API key from `Authorization: Api-Key <key>` or custom header
2. Validating key format and checking hash
3. Returning the APIKey object if valid

We'll configure it to use `Authorization: Bearer <key>` for consistency with standard patterns.

```python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # For users
        'rest_framework_api_key.permissions.HasAPIKey',  # For API keys
    ],
}
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

- **`djangorestframework-api-key`** - Primary package for API key management
  - Install: `pip install djangorestframework-api-key`
  - Docs: https://florimondmanca.github.io/djangorestframework-api-key/
- Django REST Framework (already installed)
- Django built-in auth (already available)

## Priority

**High** - Required for CLI client and hardware integration use cases.

## Related TODOs

- TODO #16: Account-Based Authentication (prerequisite)
- TODO #18: REST Endpoints for External Control (will use API key auth)
