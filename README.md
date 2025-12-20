# HealthScan

A vision-grounded AI agent that helps with healthcare documentation. Take a photo of a prescription, medical form, or insurance card, and HealthScan extracts the information, checks for drug interactions, and provides personalized diet recommendations.

## What It Does

HealthScan uses computer vision and AI to understand medical documents. It can:

- Extract prescription details from photos
- Check for drug-drug interactions across multiple prescriptions
- Provide diet recommendations based on medical conditions and medications
- Generate meal plans tailored to specific health needs

## Architecture

The system is built in three layers:

**Frontend**: Next.js web app and React Native mobile app. Users upload images and get results through a clean interface.

**Backend**: FastAPI server that handles the AI processing. It uses multimodal language models (Gemini Pro, GPT-4o) to analyze images and extract structured data.

**Core Engines**: Three specialized modules work together:

1. **Vision Engine** - Analyzes images to detect UI elements and extract text
2. **Planner Engine** - Creates step-by-step action plans based on user intent
3. **Executor Engine** - Automates browser interactions when needed

The architecture separates these concerns so each part can be optimized independently. Vision uses one AI model, planning uses another, and execution uses Playwright for browser automation.

## Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, Uvicorn
- **AI Models**: Gemini Pro 1.5, GPT-4o
- **Database**: PostgreSQL (Supabase)
- **Mobile**: React Native (Expo)

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### Frontend

```bash
cd app/frontend
npm install
npm run dev
```

Set your API keys in `.env` files (see `.env.example`).

## License

MIT
