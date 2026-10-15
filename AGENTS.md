# Project Agent Instructions

## Environment

Target: MX Linux 25 (Debian 13 / bookworm base).

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
    nodejs npm cargo \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2
```

### 2. Install Poetry (Python)

```bash
pip install --user poetry
# or: pip install poetry
```

Poetry lands in `~/.local/bin/poetry`. Add it to PATH if missing:
`export PATH="$HOME/.local/bin:$PATH"` (put that in `~/.bashrc`).

### 3. Install pnpm (Node)

```bash
npm install -g pnpm
```

### 4. Install backend dependencies

```bash
cd backend
poetry install
```

> Python 3.12 is what Poetry resolves to (`backend-...-py3.12`); `pyproject.toml`
> pins `^3.10`, which 3.12 satisfies. Just use `poetry run`.

### 5. Playwright Chromium (optional, for "Screenshot preview")

```bash
poetry run playwright install --with-deps chromium
```

### 6. API keys

Set at least one LLM key. This fork uses NVIDIA NIM by default — edit
`backend/.env` (restart the backend after editing):

```
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_API_KEY=nvapi-your-key-here
```

You can also paste keys into the in-app Settings dialog (gear icon).

## Running

```bash
# Backend (from backend/)
poetry run uvicorn main:app --reload --port 7001

# Frontend (from frontend/) — open http://localhost:5173
pnpm dev
```

The Vite dev server binds to `localhost` only — use `http://localhost:5173`,
not `http://127.0.0.1:5173`.

## Testing & type checking

```bash
cd backend && poetry run pytest
cd backend && poetry run pyright
cd frontend && pnpm lint
```

Type checking policy: no new warnings in changed files (`pyright`).
`cd frontend && pnpm lint` reports pre-existing errors (e.g.
`@typescript-eslint/no-explicit-any` in `generateCode.ts`) because lint runs
with `--max-warnings 0`; those are baseline, not environment issues.

## Prompt formatting

- Prefer triple-quoted strings (`"""..."""`) for multi-line prompt text.
- For interpolated multi-line prompts, prefer a single triple-quoted f-string
  over concatenated string fragments.

## Hosted

The hosted version is on the `hosted` branch. The `hosted` branch connects to
a saas backend, which is a separate codebase at ../screenshot-to-code-saas

## Cursor Cloud specific instructions

Dependencies are refreshed automatically on startup (`poetry install` in
`backend/`, `pnpm install` in `frontend/`); no manual install is needed.
Cursor Cloud environment setup should run
`bash /agent/repos/screenshot-to-code/scripts/cursor-cloud-install.sh`;
the script changes to the repo root before installing so it works regardless
of the startup working directory.
