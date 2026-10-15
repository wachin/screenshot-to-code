# screenshot-to-code

Convert screenshots, mockups, Figma designs, and screen recordings into clean, functional code using AI. The easiest way to try this is using <a href="https://screenshottocode.com/?utm_source=github&utm_medium=readme&utm_campaign=oss_readme&utm_content=top_cta" target="_blank" rel="noopener noreferrer">the official, hosted product at screenshottocode.com →</a>

## Local setup (MX Linux 25 / Debian 13)

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

### 2. Poetry (Python)

```bash
pip install --user poetry
# Poetry lands in ~/.local/bin/poetry. If `poetry` is not found:
export PATH="$HOME/.local/bin:$PATH"   # put this in ~/.bashrc
```

### 3. pnpm (Node)

```bash
npm install -g pnpm
```

### 4. Backend dependencies

```bash
cd backend
poetry install
```

Poetry resolves to Python 3.12 (`backend-...-py3.12`); `pyproject.toml` pins
`^3.10`, which 3.12 satisfies. Just use `poetry run`.

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

## Using a custom OpenAI-compatible API (NVIDIA NIM, local proxies, etc.)

This fork lets you route code generation through any OpenAI-compatible
endpoint by setting `OPENAI_BASE_URL`. The backend uses the OpenAI Python
client pointed at that URL, so services like [NVIDIA NIM](https://build.nvidia.com/)
(`https://integrate.api.nvidia.com/v1`), LM Studio, Ollama, or any proxy work.

### NVIDIA NIM example

1. Get a key at https://build.nvidia.com/ and set it in `backend/.env`:

   ```bash
   cd backend
   echo "OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1" > .env
   echo "OPENAI_API_KEY=nvapi-your-key-here" >> .env
   ```

   (You can also paste the key into the settings dialog in the frontend — the
   gear icon after loading the app.)

2. Start the backend:

   ```bash
   poetry run uvicorn main:app --reload --port 7001
   ```

3. Open the frontend at http://localhost:5173 and take a screenshot.

The model used is `deepseek-ai/deepseek-v4.1-flash` (NVIDIA). It supports
text + image input, so screenshot-to-code works. Tools that call other
providers (`extract_assets` → Gemini, `edit_images`/`remove_backgrounds` →
Replicate) are only available when those keys are set.

### Notes

- The backend picks models automatically based on which keys you have. With
  only an NVIDIA key it uses `deepseek-ai/deepseek-v4.1-flash`.
- If your endpoint returns a pricing response, cost tracking works; otherwise
  the variant is treated as unpriced (no spend ceiling).
- Some endpoints reject the `reasoning` parameter; the NVIDIA provider in this
  fork omits it.

## Docker

If you have Docker installed, run this from the root directory:

```bash
echo "OPENAI_API_KEY=sk-your-key" > .env
docker-compose up -d --build
```

The app will be up and running at http://localhost:5173. Note that you can't develop the application with this setup, as file changes won't trigger a rebuild.

## 🙋‍♂️ FAQs

- **I'm running into an error when setting up the backend. How can I fix it?** [Try this](https://github.com/abi/screenshot-to-code/issues/3#issuecomment-1814777959). If that still doesn't work, open an issue.
- **How do I get an OpenAI API key?** See https://github.com/abi/screenshot-to-code/blob/main/Troubleshooting.md
- **How can I configure an OpenAI proxy?** If you're not able to access the OpenAI API directly, for example because of country restrictions, you can try a VPN or configure the OpenAI base URL to use a proxy. Set `OPENAI_BASE_URL` in `backend/.env` or directly in the UI in the settings dialog. Make sure the URL has `v1` in the path, for example: `https://xxx.xxxxx.xxx/v1`.
- **How can I update the backend host that my frontend connects to?** Configure `VITE_HTTP_BACKEND_URL` and `VITE_WS_BACKEND_URL` in `frontend/.env.local`. For example, set `VITE_HTTP_BACKEND_URL=http://124.10.20.1:7001`.
- **Seeing UTF-8 errors when running the backend?** On Windows, open the `.env` file with Notepad++, then go to Encoding and select UTF-8.
- **How can I provide feedback?** For feedback, feature requests, and bug reports, open an issue or ping me on [Twitter](https://twitter.com/_abi_).

## Supported stacks

- HTML + Tailwind
- HTML + CSS
- React + Tailwind
- Vue + Tailwind
- Bootstrap
- Ionic + Tailwind

## Default AI models

- Gemini 3 Flash Preview and Gemini 3.1 Pro Preview - the best models
- GPT-5.5 and GPT-5.4 Mini
- Claude Opus 4.6, Claude Opus 4.8
- z-image-turbo (using Replicate) for image generation

## 📚 Examples

Screenshot to Code also supports taking a screen recording of a website in action and turning that into a functional prototype.

![google in app quick 3](https://github.com/abi/screenshot-to-code/assets/23818/8758ffa4-9483-4b9b-bb66-abd6d1594c33)

**NYTimes**

| Original                                                                                                                                                        | Replica                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <img width="1238" alt="Screenshot 2023-11-20 at 12 54 03 PM" src="https://github.com/user-attachments/assets/6b0ae86c-1b0f-4598-a578-c7b62205b3e2"> | <img width="1435" height="737" alt="Screenshot 2026-06-15 at 3 06 37 PM" src="https://github.com/user-attachments/assets/48f0ab94-5fdc-41e7-ad6e-b4ad7ef69ae1" /> |


**Instagram**

https://github.com/user-attachments/assets/a335a105-f9cc-40e6-ac6b-64e5390bfc21

**Hacker News**


https://github.com/user-attachments/assets/205cb5c7-9c3c-438d-acd4-26dfe6e077e5
