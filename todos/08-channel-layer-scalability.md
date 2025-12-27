# InMemoryChannelLayer Won't Scale

## Issue
`service/quizzer/settings.py:80-84` uses in-memory channel layer for Django Channels.

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```

## Problems
- Only works with single server process
- Can't run multiple Daphne workers
- Lost messages if process restarts
- No horizontal scaling possible
- Fine for development, broken for production

## When This Becomes a Problem
- Multiple games running simultaneously with many players
- Want to run multiple workers for redundancy
- Deploy to cloud with auto-scaling
- Need process isolation

## Solution
Use Redis-backed channel layer:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

## Action Items
- [ ] Add `channels-redis` to requirements.txt
- [ ] Document Redis setup in README
- [ ] Create docker-compose.yml with Redis service
- [ ] Add Redis configuration (environment-based)
- [ ] Test with multiple workers
- [ ] Update deployment docs

## Priority
Low for now (development only), but plan before production deployment.
