# Setup Checklist

## Prerequisites
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] OpenAI API key
- [ ] Supabase account

## Frontend Setup
- [ ] `cd app/frontend`
- [ ] `npm install`
- [ ] Create `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] `npm run dev`

## Backend Setup
- [ ] `cd backend`
- [ ] `pip3 install -r requirements.txt`
- [ ] `playwright install chromium`
- [ ] Create `.env` file with:
  - `OPENAI_API_KEY=sk-...`
  - `DATABASE_URL=postgresql://...`
  - `FRONTEND_URL=http://localhost:3000`
  - `JWT_SECRET=your-secret-key`
  - `ALLOWED_DOMAINS=example.com`
- [ ] `python3 init_db.py`
- [ ] `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`

## Mobile Setup (Optional)
- [ ] `cd mobile`
- [ ] `npm install`
- [ ] Create `.env` with `EXPO_PUBLIC_API_URL=http://YOUR_IP:8000`
- [ ] `npx expo start`

## Supabase Setup
- [ ] Create project at supabase.com
- [ ] Get connection string from Settings → Database
- [ ] Update `DATABASE_URL` in `backend/.env`
- [ ] Run `python3 backend/init_db.py`

## Verify
- [ ] Frontend: http://localhost:3000
- [ ] Backend: http://localhost:8000/health
- [ ] Test image upload
- [ ] Test drug interaction checker
- [ ] Test diet portal

