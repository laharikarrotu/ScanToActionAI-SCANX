# Requirements & Setup Guide

## System Requirements

### Hardware
- **RAM**: 16GB minimum (for Playwright browser automation)
- **Storage**: 10GB free space
- **OS**: macOS, Linux, or Windows

### Software
- **Node.js**: 18+ (install via [nvm](https://github.com/nvm-sh/nvm))
- **Python**: 3.11+ (check: `python3 --version`)
- **Git**: Latest version
- **Package Managers**: npm, pip3

## API Keys & Services

### Required
1. **OpenAI API Key**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Get API key from API Keys section
   - Add credits ($5-10 for testing)

2. **Supabase Account**
   - Sign up at [supabase.com](https://supabase.com)
   - Create new project
   - Get database connection string

### Optional
- **Anthropic API Key** (for Claude)
- **Google API Key** (for Gemini)
- **Vercel Account** (for frontend deployment)
- **Railway Account** (for backend deployment)

## Installation Checklist

### ✅ Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd ScanToActionAI-SCANX
```

### ✅ Step 2: Frontend Setup
```bash
cd app/frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```
**Verify**: Open http://localhost:3000

### ✅ Step 3: Backend Setup
```bash
cd backend
pip3 install -r requirements.txt
playwright install chromium
```

**Create `.env` file:**
```bash
cat > .env << EOF
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://postgres:password@host:port/dbname
FRONTEND_URL=http://localhost:3000
JWT_SECRET=your-secret-key-min-32-chars
ALLOWED_DOMAINS=example.com
EOF
```

**Initialize database:**
```bash
python3 init_db.py
```

**Run server:**
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
**Verify**: Open http://localhost:8000/health

### ✅ Step 4: Mobile Setup (Optional)
```bash
cd mobile
npm install
echo "EXPO_PUBLIC_API_URL=http://YOUR_LOCAL_IP:8000" > .env
npx expo start
```

**Find your local IP:**
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

## Data Structures to Learn

### Currently Used:
- **Lists/Arrays**: `List[str]`, `List[Medication]` - Collections
- **Dictionaries**: `Dict[str, Any]` - Key-value pairs for configs
- **Sets**: `set()` - Unique collections (domains, patterns)
- **Tuples**: `(str, int)` - Immutable pairs
- **Pydantic Models**: Type-safe data structures

### Recommended to Learn:
- **Trees**: For nested JSON structures
- **Graphs**: For medication interaction networks
- **Hash Tables**: Understanding dictionary internals
- **Queues**: For task processing (future: Celery)

## System Design Topics

### Implemented:
1. **API Gateway Pattern** - FastAPI as single entry point
2. **Microservices** - Separate modules (vision, planner, executor)
3. **Async Processing** - Non-blocking I/O
4. **Database Design** - Relational schema (SQLAlchemy)
5. **Error Handling** - Try-catch with fallbacks
6. **CORS & Security** - Multi-origin, JWT auth
7. **Logging** - Event-based logging system

### To Learn/Implement:
1. **Message Queues** - Redis + Celery for background tasks
2. **Caching** - Redis for LLM response caching
3. **Load Balancing** - Multiple backend instances
4. **Rate Limiting** - Per-user API limits
5. **Circuit Breakers** - LLM API failure handling
6. **Database Indexing** - Optimize queries
7. **CDN** - Static asset delivery
8. **Monitoring** - Prometheus/Grafana

## Common Issues & Fixes

### Issue: "Module not found"
**Fix**: Install dependencies
```bash
cd backend && pip3 install -r requirements.txt
cd ../app/frontend && npm install
```

### Issue: "Playwright browser not found"
**Fix**: Install browsers
```bash
cd backend && playwright install chromium
```

### Issue: "CORS error"
**Fix**: Update `FRONTEND_URL` in `backend/.env`

### Issue: "Database connection failed"
**Fix**: Check Supabase connection string, ensure database is accessible

### Issue: "OpenAI API error"
**Fix**: Check API key, ensure account has credits

## Testing Checklist

- [ ] Frontend loads at http://localhost:3000
- [ ] Backend health check: http://localhost:8000/health
- [ ] Can upload image in frontend
- [ ] Backend processes image and returns response
- [ ] Drug interaction checker works
- [ ] Diet portal generates recommendations
- [ ] Database connection works
- [ ] Mobile app connects to backend (if using)

## Deployment Checklist

### Frontend (Vercel)
- [ ] Connect GitHub repo
- [ ] Set root directory: `app/frontend`
- [ ] Add env var: `NEXT_PUBLIC_API_URL`
- [ ] Deploy

### Backend (Railway/Render)
- [ ] Connect GitHub repo
- [ ] Set root directory: `backend`
- [ ] Add all env vars from `.env`
- [ ] Install Playwright: `playwright install chromium`
- [ ] Deploy

### Database (Supabase)
- [ ] Create project
- [ ] Get connection string
- [ ] Run migrations: `python3 init_db.py`
- [ ] Test connection

## Next Steps

1. **Development**: Test all features locally
2. **Deployment**: Deploy to Vercel + Railway
3. **Testing**: Test with real medical forms (test data)
4. **Optimization**: Add caching, improve latency
5. **Features**: Add more healthcare use cases

