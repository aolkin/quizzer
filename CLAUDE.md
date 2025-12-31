# Instructions for AI Agents and Assistants

**IMPORTANT**: When making ANY code changes to this repository, you MUST follow these quality checks:

## Required Quality Checks Before Committing

### 1. Backend (Python/Django) - `/service`

**Linting & Formatting:**
```bash
cd service
uv run black --check .
uv run flake8 .
```

**Note:** Configuration is in `service/pyproject.toml` (Black) and `service/.flake8` (Flake8).

**Testing:**
```bash
cd service
uv run python manage.py test
```

**Install dependencies if needed:**
```bash
cd service
uv sync --all-extras
```

### 2. Frontend (TypeScript/Svelte) - `/app`

**Linting:**
```bash
cd app
bun run lint
```

**Type Checking:**
```bash
cd app
bun run check
```

**Unit Testing:**
```bash
cd app
bun run test
```

**E2E Testing (Playwright):**
```bash
cd app
npm run test:e2e      # Run E2E tests (starts backend automatically)
npm run test:e2e:ui   # Run with interactive UI
```

**Build Verification:**
```bash
cd app
bun run build
```

**Install dependencies if needed:**
```bash
cd app
bun install
npx playwright install chromium  # For E2E tests
```

## Why This Matters

- **Prevent CI failures**: These same checks run in GitHub Actions CI/CD
- **Code quality**: Ensures consistent formatting and catches errors early
- **No regressions**: Tests verify existing functionality still works
- **Faster iteration**: Catch issues locally before pushing

## Quick Reference

All checks in one place:

```bash
# Backend
cd service && uv run black --check . && uv run flake8 . && uv run python manage.py test && cd ..

# Frontend (unit tests + build)
cd app && bun run lint && bun run check && bun run test && bun run build && cd ..

# Frontend E2E tests (optional, runs in CI)
cd app && npm run test:e2e && cd ..
```

## Pre-commit Hooks (Optional but Recommended)

Install pre-commit hooks to automatically run checks:
```bash
uv tool install pre-commit
pre-commit install
```

## Testing Philosophy

When writing tests, follow our testing philosophy documented in [TESTING.md](TESTING.md):
- Focus on **high-value tests** that verify complex logic and prevent regressions
- Avoid trivial tests for simple setters/getters or framework behavior
- Test behavior, not implementation
- Mock external dependencies (WebSocket, fetch, database) in unit tests
- Use E2E tests (Playwright) for multi-client synchronization and integration testing

## Code Style

- **Write self-explanatory code**: Code should be clear enough that it doesn't need comments
- **Avoid unnecessary comments**: Only add comments when explaining complex algorithms, business logic, or non-obvious decisions
- **Use docstrings sparingly**: Only for public APIs and complex functions where the purpose isn't obvious from the name
- **Prefer meaningful names**: Use descriptive variable, function, and class names instead of comments

## More Information

For complete development guidelines and workflow, see [README.md](README.md).
