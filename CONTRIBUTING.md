# Contributing to Quizzer

Thank you for your interest in contributing to Quizzer! This document provides guidelines for developers and AI assistants working on this project.

## For AI Agents and Assistants

**IMPORTANT**: When making code changes to this repository, you MUST:

1. **Run the linter** before committing:
   - Backend (Python): `cd service && black . && flake8 .`
   - Frontend (TypeScript/Svelte): `cd app && bun run lint`

2. **Run type checking** (Frontend):
   - `cd app && bun run check`

3. **Run tests** to ensure no regressions:
   - Backend: `cd service && python manage.py test`
   - Frontend: `cd app && bun run test`

4. **Run the build** to ensure no build errors:
   - Frontend: `cd app && bun run build`

These steps are automated in CI/CD, but running them locally ensures quality code and faster iteration.

## Development Workflow

### Initial Setup

1. **Install pre-commit hooks** (recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```
   This will automatically run linters and formatters before each commit.

2. **Backend Setup**:
   ```bash
   cd service
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Frontend Setup**:
   ```bash
   cd app
   bun install
   ```

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**, following the code style:
   - Python: Follow PEP 8, Black formatting (max line length: 100)
   - TypeScript/Svelte: ESLint + Prettier formatting
   - Write tests for new features and bug fixes

3. **Run quality checks locally**:
   ```bash
   # Backend
   cd service
   black --check --line-length=100 .
   flake8 . --max-line-length=100 --extend-ignore=E203,W503
   python manage.py test
   
   # Frontend
   cd app
   bun run lint
   bun run check
   bun run test
   bun run build
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```
   Pre-commit hooks will automatically run if installed.

5. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Quality Standards

### Testing Philosophy

See [app/TESTING.md](app/TESTING.md) for detailed testing guidelines. In summary:
- Focus on **high-value tests** that verify complex logic
- Avoid trivial tests for simple setters/getters
- Test behavior, not implementation
- Keep tests readable and maintainable

### Code Coverage

- Backend: Aim for 80%+ code coverage
- Frontend: Focus on testing critical paths and complex logic
- Coverage reports are generated in CI

### Code Style

**Python (Backend)**:
- Use Black formatter with 100-character line length
- Follow PEP 8 conventions
- Use type hints where appropriate
- Write docstrings for public APIs

**TypeScript/Svelte (Frontend)**:
- Use ESLint + Prettier for formatting
- Follow TypeScript best practices
- Use type annotations
- Keep components focused and single-purpose

## Continuous Integration

All pull requests are automatically checked by GitHub Actions:

- **Backend CI**: Linting (Black, Flake8), tests, coverage
- **Frontend CI**: Linting (ESLint, Prettier), type checking, tests, build

All checks must pass before merging.

## Project Structure

```
quizzer/
├── app/              # SvelteKit frontend
│   ├── src/         # Source code
│   └── static/      # Static assets
├── service/         # Django backend
│   ├── game/        # Game app
│   └── quizzer/     # Project settings
└── hardware/        # Raspberry Pi buzzer system
```

## Running the Application

### Development Mode

**Backend** (runs on http://localhost:8000):
```bash
cd service
python manage.py runserver
```

**Frontend** (runs on http://localhost:5173):
```bash
cd app
bun run dev
```

### Production Build

**Frontend**:
```bash
cd app
bun run build
bun run preview
```

## Getting Help

- Check existing issues and pull requests
- Review documentation in README.md
- Examine existing tests for examples
- Follow the testing philosophy in app/TESTING.md

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
