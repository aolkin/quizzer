# Instructions for AI Agents and Assistants

**IMPORTANT**: When making ANY code changes to this repository, you MUST follow these quality checks:

## Required Quality Checks Before Committing

### 1. Backend (Python/Django) - `/service`

**Linting & Formatting:**
```bash
cd service
black --check .
flake8 .
```

**Note:** Configuration is in `service/pyproject.toml` (Black) and `service/.flake8` (Flake8).

**Testing:**
```bash
cd service
python manage.py test
```

**Install dependencies if needed:**
```bash
cd service
pip install -r requirements.txt
pip install black flake8
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

**Testing:**
```bash
cd app
bun run test
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
cd service && black --check . && flake8 . && python manage.py test && cd ..

# Frontend
cd app && bun run lint && bun run check && bun run test && bun run build && cd ..
```

## Pre-commit Hooks (Optional but Recommended)

Install pre-commit hooks to automatically run checks:
```bash
pip install pre-commit
pre-commit install
```

## Testing Philosophy

When writing tests, follow our testing philosophy documented in [TESTING.md](TESTING.md):
- Focus on **high-value tests** that verify complex logic and prevent regressions
- Avoid trivial tests for simple setters/getters or framework behavior
- Test behavior, not implementation
- Mock external dependencies (WebSocket, fetch, database)

## More Information

For complete development guidelines and workflow, see [README.md](README.md).
