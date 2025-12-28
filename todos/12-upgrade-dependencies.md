# Upgrade Dependencies to Latest Versions

## Issue
While major framework versions are current, minor and patch versions should be updated for bug fixes and improvements.

## Current Status

### Frontend (package.json)
All major versions are latest, but minor/patch versions may be outdated:
- Svelte: `^5.16.0` (check for 5.x updates)
- SvelteKit: `^2.15.1` (check for 2.x updates)
- TypeScript: `^5.7.2` (check for 5.x updates)
- TailwindCSS: `^3.4.17` (v4 is beta, stay on 3.x for now)
- Vite: `^5.4.11` (check for 5.x updates)
- Vitest: `^2.1.8` (check for 2.x updates)
- ESLint: `^9.17.0` (check for 9.x updates)
- And all other frontend packages

### Backend (requirements.txt - once created)
- Django: `5.1.4` → Check for 5.1.x updates
- django-channels → Check latest 4.x
- djangorestframework → Check latest 3.x
- daphne → Check latest version
- django-colorfield → Check latest version
- django-cors-headers → Check latest version

### Hardware (requirements.txt - once created)
- websockets → Check latest version
- RPi.GPIO → Check latest version (if still maintained)

## Why This Matters
- Security patches in minor/patch releases
- Bug fixes
- Performance improvements
- New features within same major version
- Stay current to make future major version upgrades easier

## Approach

### Frontend
```bash
cd app

# Check outdated packages
bun outdated

# Update all to latest compatible versions (respecting ^)
bun update

# Or update specific packages
bun update svelte @sveltejs/kit vite
```

### Backend
```bash
cd service

# Once requirements.txt exists
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt

# Update requirements.txt with new versions
pip freeze > requirements.txt
```

### Caution Areas
- **TailwindCSS**: Stay on 3.x (v4 is still in beta/alpha)
- **Major version jumps**: If any package has crossed major version, review breaking changes
- **Svelte 5**: Already on latest major, but check for Svelte 5.x updates (runes API still evolving)

## Testing After Updates
- [ ] Frontend builds without errors (`bun run build`)
- [ ] Type checking passes (`bun run check`)
- [ ] Linting passes (`bun run lint`)
- [ ] All tests pass (`bun run test`)
- [ ] Backend tests pass (`python manage.py test`)
- [ ] Dev server runs (`bun run dev` and `python manage.py runserver`)
- [ ] Manual smoke testing of key features

## Action Items

### Preparation
- [ ] Ensure requirements.txt exists (see TODO #01)
- [ ] Ensure all tests pass on current versions (see TODOs #08, #09)
- [ ] Commit current state before upgrading

### Frontend Updates
- [ ] Run `bun outdated` to see available updates
- [ ] Review changelog for any breaking changes
- [ ] Run `bun update` to update all packages
- [ ] Test build and type checking
- [ ] Run all tests
- [ ] Commit updated package.json and lockfile

### Backend Updates
- [ ] Run `pip list --outdated`
- [ ] Review Django 5.1.x release notes
- [ ] Update packages individually or via pip-tools
- [ ] Update requirements.txt
- [ ] Run migrations if needed
- [ ] Test backend
- [ ] Commit updated requirements.txt

### Hardware Updates
- [ ] Check websockets package for updates
- [ ] Check RPi.GPIO (or consider alternatives like gpiozero)
- [ ] Update hardware/requirements.txt
- [ ] Test on actual Raspberry Pi if possible

### Documentation
- [ ] Update README if any setup instructions change
- [ ] Note any deprecated features to avoid
- [ ] Document version numbers in requirements files

## Frequency
- **Minor/patch updates**: Every 2-3 months
- **Security updates**: Immediately when announced
- **Major version updates**: Evaluate carefully, plan migration

## Tools to Help
- **Frontend**: `bun outdated`, `npm-check-updates`
- **Backend**: `pip list --outdated`, `pip-review`, `pip-tools`
- **Automation**: Dependabot (GitHub) can create PRs for updates
- **Security**: `npm audit`, `pip-audit` for vulnerability scanning

## Success Criteria
- All packages on latest compatible minor/patch versions
- No security vulnerabilities (`npm audit`, `pip-audit`)
- All tests pass
- Application runs without regressions
- Dependencies documented in requirements files
