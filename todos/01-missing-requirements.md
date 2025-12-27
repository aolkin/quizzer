# Missing requirements.txt

## Issue
Backend dependencies aren't tracked in version control. The README even mentions this as a TODO.

## Impact
- Impossible to set up the project without guessing dependencies
- Version mismatches between environments
- Unclear what packages are actually needed

## Required Dependencies
Based on imports and settings.py:
- Django>=5.1
- djangorestframework
- django-cors-headers
- channels
- daphne
- django-colorfield
- websockets (for hardware client)

## Action Items
- [ ] Create `service/requirements.txt` with all backend dependencies
- [ ] Test fresh install in clean virtual environment
- [ ] Consider adding version pins for reproducible builds
- [ ] Create `hardware/requirements.txt` for buzzer dependencies
