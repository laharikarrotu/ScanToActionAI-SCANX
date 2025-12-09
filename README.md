# SCANX

Building an AI agent that can look at screenshots/photos and actually do stuff. Take a picture of a booking page, tell it "book this for me", and it figures out what buttons to click and forms to fill.

Still a work in progress, but the core idea is working.

## What it does

You send it an image (from your phone camera or screenshot) + what you want to do, and it:
1. Uses a vision LLM to understand what's on the screen
2. Plans out the steps needed
3. Actually executes them using Playwright (browser automation)

Right now it's focused on web interfaces, but the architecture should work for other stuff too.

## Stack

**Frontend:**
- Next.js 15 (React + TypeScript)
- Tailwind CSS
- shadcn/ui for components

**Backend:**
- FastAPI (Python)
- GPT-4o / Claude / Gemini for vision + planning
- Playwright for browser automation
- SQLite for now, probably Postgres later

## Setup

You'll need Node.js 18+, Python 3.11+, and Playwright.

```bash
# Frontend
cd app/frontend
npm install
npm run dev

# Backend (separate terminal)
cd backend
pip install -r requirements.txt
playwright install
uvicorn api.main:app --reload
```

Set up `.env` files with your API keys. Check the `.env.example` files for what's needed.

## Project structure

```
app/frontend/     # Next.js app
backend/
  api/           # FastAPI routes
  vision/        # UI detection
  planner/       # Action planning
  executor/      # Playwright automation
  memory/        # Logs and storage
```

## Current status

- ✅ Basic architecture in place
- ✅ Vision engine working with GPT-4o
- ✅ Planner generating action steps
- 🚧 Executor needs more work (selector matching is tricky)
- 🚧 Frontend is basic, needs polish
- ❌ Memory/learning not implemented yet

## Notes

- Using test mode for any payment stuff (Stripe test mode)
- Only works on allowed domains for safety
- Sensitive data (passwords, cards) gets redacted before logging
- Latency is usually 5-12 seconds per workflow, depends on the LLM

## Why I'm building this

Wanted to see if I could make an agent that actually understands visual interfaces and can act on them, not just chat about them. Also planning to demo this at CES if it works out.

Built on a MacBook Pro 16GB, works fine for development. Deployed frontend on Vercel, backend on Railway for demos.

