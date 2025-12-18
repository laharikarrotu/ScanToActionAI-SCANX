# Deployment Guide

## Quick Deploy Checklist

### Frontend (Vercel)
- [ ] Push code to GitHub
- [ ] Connect repo to Vercel
- [ ] Set root directory: `app/frontend`
- [ ] Add env var: `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
- [ ] Deploy

### Backend (Railway/Render)
- [ ] Push code to GitHub
- [ ] Connect repo to Railway/Render
- [ ] Set root directory: `backend`
- [ ] Add env vars:
  - `OPENAI_API_KEY`
  - `DATABASE_URL` (Supabase)
  - `FRONTEND_URL` (your Vercel URL)
  - `JWT_SECRET`
  - `ALLOWED_DOMAINS`
- [ ] Install Playwright: Add build command: `playwright install chromium`
- [ ] Deploy

### Database (Supabase)
- [ ] Already set up
- [ ] Verify connection string in backend env vars
- [ ] Test connection

## Environment Variables

### Production Frontend (.env.production)
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Production Backend
```
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
FRONTEND_URL=https://your-app.vercel.app
JWT_SECRET=strong-random-secret-here
ALLOWED_DOMAINS=your-app.vercel.app
```

## Post-Deployment

1. Test all endpoints
2. Verify CORS is working
3. Test image uploads
4. Test drug interaction checker
5. Test diet portal
6. Monitor logs for errors

