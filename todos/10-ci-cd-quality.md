# CI/CD and Code Quality Automation

## Issue
No automated checks for code quality, testing, or deployment readiness.

## Current State
- No GitHub Actions workflows
- No pre-commit hooks
- No linting enforcement
- No test automation
- No coverage reporting
- Manual PR review without automated checks

## Why This Matters
- Catch bugs before they reach main branch
- Enforce code style consistency
- Prevent commits that break tests
- Automated quality gates for PRs
- Faster feedback loop for developers

## Components to Add

### 1. Pre-commit Hooks
Use `pre-commit` framework to run checks before commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict

  # Python backend
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        files: ^service/

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        files: ^service/
        args: ['--max-line-length=100']

  # Frontend
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        files: \.(js|ts|svelte|json|css)$
        args: ['--write']
```

### 2. GitHub Actions - Backend CI

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd service
          pip install -r requirements.txt
          pip install coverage

      - name: Run tests with coverage
        run: |
          cd service
          coverage run --source='.' manage.py test
          coverage report --fail-under=80
          coverage xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./service/coverage.xml

  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install linters
        run: pip install black flake8

      - name: Run black
        run: black --check service/

      - name: Run flake8
        run: flake8 service/ --max-line-length=100
```

### 3. GitHub Actions - Frontend CI

```yaml
# .github/workflows/frontend-ci.yml
name: Frontend CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install dependencies
        run: |
          cd app
          bun install

      - name: Run linter
        run: |
          cd app
          bun run lint

      - name: Type check
        run: |
          cd app
          bun run check

      - name: Run tests with coverage
        run: |
          cd app
          bun run test -- --coverage

      - name: Build
        run: |
          cd app
          bun run build
```

### 4. Branch Protection Rules
Configure on GitHub:
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require review from code owners (optional)
- Require passing CI checks:
  - Backend CI
  - Frontend CI
  - Test coverage thresholds

### 5. Additional Quality Tools

**Backend:**
- `mypy` for Python type checking
- `pylint` for additional linting
- `bandit` for security checks
- `django-coverage-plugin` for template coverage

**Frontend:**
- ESLint with TypeScript rules
- Prettier for formatting
- `svelte-check` for Svelte validation

## Action Items

### Setup Phase
- [ ] Create requirements.txt (see TODO #01)
- [ ] Install pre-commit framework: `pip install pre-commit`
- [ ] Create `.pre-commit-config.yaml`
- [ ] Run `pre-commit install` in repo
- [ ] Test pre-commit hooks locally

### GitHub Actions
- [ ] Create `.github/workflows/` directory
- [ ] Add backend-ci.yml workflow
- [ ] Add frontend-ci.yml workflow
- [ ] Test workflows on a feature branch
- [ ] Add status badges to README

### Branch Protection
- [ ] Enable branch protection on main branch
- [ ] Require CI checks to pass
- [ ] Require coverage thresholds (80%+)
- [ ] Configure PR review requirements

### Quality Metrics
- [ ] Set up Codecov or similar for coverage tracking
- [ ] Add coverage badges to README
- [ ] Configure coverage thresholds (fail if below 80%)
- [ ] Add linting status badges

### Documentation
- [ ] Document pre-commit setup in README
- [ ] Add contributing guidelines (CONTRIBUTING.md)
- [ ] Document how to run tests locally
- [ ] Document CI/CD pipeline

## Success Criteria
- All PRs automatically run tests and linting
- Coverage stays above 80%
- Pre-commit hooks prevent badly formatted commits
- Green CI badges on README
- Developers can run same checks locally that CI runs

## Benefits
✅ Catch bugs before code review
✅ Consistent code formatting
✅ Prevent regressions
✅ Faster PR review (automated checks)
✅ Higher confidence in main branch
✅ Documentation of quality standards
