# Contributing

## Setup
```
git clone https://github.com/Nemo-22-UF/CEN3031-Project.git
cd CEN3031-Project
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
python run.py
```
Open http://127.0.0.1:5000

## Workflow
1. `main` is always runnable. Nobody pushes directly to it.
2. Pick an issue from the project board and move it to In Progress.
3. Create a branch from `main`:
   - `feature/<issue#>-short-name`
   - `fix/<issue#>-short-name`
   - `docs/<issue#>-short-name`
4. Commit often with clear messages (see below).
5. Push and open a pull request. Link the issue with `Closes #<issue#>`.
6. One teammate reviews and approves. CI must pass.
7. Squash and merge. Delete the branch.

## Commit messages
Format: `type: short description`

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Examples:
- `feat: add user registration form`
- `fix: correct lesson progress calculation`
- `docs: update setup instructions`

## Before opening a PR
- `git pull origin main` and resolve conflicts
- `pytest` passes
- No `.env`, `venv/`, or `__pycache__/` committed

## Project structure
```
app/            Flask application (routes, templates, static files)
tests/          pytest tests
docs/           project documentation
config.py       configuration loaded from environment variables
run.py          entry point
```
