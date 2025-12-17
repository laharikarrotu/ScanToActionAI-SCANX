# HealthScan

AI-powered healthcare assistant that helps you navigate medical forms, prescriptions, and healthcare paperwork. Take a picture of a medical form, prescription, or insurance card, and HealthScan helps you fill it out, understand it, or take action.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │  Web (Next.js)   │         │ Mobile (Expo)    │           │
│  │  - Form Scanner  │         │  - Camera        │           │
│  │  - Interactions  │         │  - Prescriptions │           │
│  │  - Diet Portal   │         │  - Food Check    │           │
│  └────────┬─────────┘         └────────┬─────────┘           │
└───────────┼─────────────────────────────┼──────────────────────┘
            │ HTTPS                        │ HTTPS
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                        │
│  - Authentication (JWT)                                          │
│  - CORS & Rate Limiting                                          │
│  - Request Validation                                            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CORE ENGINE LAYER                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   VISION     │  │   PLANNER    │  │   EXECUTOR   │          │
│  │   ENGINE     │  │   ENGINE     │  │   ENGINE     │          │
│  │              │  │              │  │              │          │
│  │ - UI Detect  │  │ - Task Plan  │  │ - Browser    │          │
│  │ - Extract    │  │ - Steps      │  │   Automation│          │
│  │ - OCR        │  │ - Validation │  │ - API Calls │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  [GPT-4o Vision]    [GPT-4o Reasoning]  [Playwright]            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ MEDICATION   │  │  NUTRITION   │  │   MEMORY     │          │
│  │   MODULE     │  │    MODULE     │  │   LAYER      │          │
│  │              │  │              │  │              │          │
│  │ - Extract    │  │ - Diet Recs  │  │ - Event Logs │          │
│  │ - Interactions│ │ - Food Check │  │ - Database   │          │
│  │ - Checker    │  │ - Meal Plans │  │ - Storage   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE & MEMORY                              │
│  - PostgreSQL (Supabase) - User data, logs, sessions            │
│  - JSON Event Logs - Audit trails                               │
│  - File Storage - Screenshots, uploads                          │
└─────────────────────────────────────────────────────────────────┘
```

### Component Flow

1. **User Input** → Frontend captures image + intent
2. **Vision Engine** → LLM analyzes image, extracts UI elements/medication info
3. **Planner Engine** → LLM creates step-by-step action plan
4. **Executor Engine** → Playwright executes actions (or returns recommendations)
5. **Memory Layer** → Logs events, stores results
6. **Response** → Frontend displays results/confirmation

## 🛠️ Tech Stack

**Frontend:**
- Next.js 15 (React + TypeScript)
- Tailwind CSS
- Expo (React Native) for mobile

**Backend:**
- FastAPI (Python) - Async API framework
- GPT-4o / Claude / Gemini - Vision + Reasoning LLMs
- Playwright - Browser automation
- PostgreSQL (Supabase) - Database
- SQLAlchemy - ORM

**Infrastructure:**
- Vercel - Frontend hosting
- Railway/Render - Backend hosting
- Supabase - Database + Auth (optional)

## 📊 Data Structures & Algorithms

### Data Structures Used:
- **Lists/Arrays**: Medication lists, action steps, UI elements
- **Dictionaries/HashMaps**: UI schemas, interaction databases, configuration
- **Trees**: JSON structures for nested data (plans, schemas)
- **Graphs**: Medication interaction networks (implicit)
- **Sets**: Allowed domains, sensitive patterns for redaction
- **Queues**: Task execution queues (future: Celery/Redis)

### Algorithms & Patterns:
- **Graph Traversal**: Drug interaction checking (pairwise comparisons)
- **String Matching**: Sensitive data redaction (pattern matching)
- **Search Algorithms**: Element selector matching in Playwright
- **Async/Await Patterns**: Concurrent LLM calls, I/O operations
- **State Machines**: Execution flow (vision → plan → execute)
- **Caching**: LLM response caching (future optimization)

## 🏛️ System Design Topics

### Implemented:
- **Microservices Architecture**: Separate modules (vision, planner, executor)
- **API Gateway Pattern**: FastAPI as single entry point
- **Async Processing**: Non-blocking I/O for LLM calls
- **Database Design**: Relational schema (users, sessions, logs)
- **Error Handling**: Try-catch with graceful degradation
- **CORS & Security**: Multi-origin support, JWT auth
- **Logging & Observability**: Event logging, audit trails

### To Implement:
- **Message Queues**: Redis/Celery for background tasks
- **Caching Layer**: Redis for LLM responses, UI schemas
- **Load Balancing**: Multiple backend instances
- **Rate Limiting**: Per-user API limits
- **Circuit Breakers**: LLM API failure handling
- **Database Sharding**: Scale storage (if needed)
- **CDN**: Static asset delivery
- **Monitoring**: Prometheus/Grafana for metrics

## 🚀 Setup & Requirements

### Prerequisites

**System Requirements:**
- macOS / Linux / Windows
- Node.js 18+ (use nvm: `nvm install 18`)
- Python 3.11+ (`python3 --version`)
- Git
- 16GB RAM recommended (for Playwright)

**API Keys Needed:**
- OpenAI API key (for GPT-4o vision)
- Supabase project (for database)
- Optional: Anthropic (Claude), Google (Gemini)

### Installation Steps

#### 1. Clone & Setup
```bash
git clone <your-repo>
cd ScanToActionAI-SCANX
```

#### 2. Frontend Setup
```bash
cd app/frontend
npm install
# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev  # Runs on http://localhost:3000
```

#### 3. Backend Setup
```bash
cd backend
pip3 install -r requirements.txt
playwright install chromium

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:password@host:port/dbname
FRONTEND_URL=http://localhost:3000
JWT_SECRET=your-secret-key-here
ALLOWED_DOMAINS=example.com
EOF

# Initialize database (if using Supabase)
python3 init_db.py

# Run server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Mobile Setup (Optional)
```bash
cd mobile
npm install
# Create .env
echo "EXPO_PUBLIC_API_URL=http://YOUR_IP:8000" > .env
npx expo start
```

### Environment Variables

**Frontend (`app/frontend/.env.local`):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend (`backend/.env`):**
```
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
FRONTEND_URL=http://localhost:3000
JWT_SECRET=change-me-in-production
ALLOWED_DOMAINS=example.com,test.com
```

**Mobile (`mobile/.env`):**
```
EXPO_PUBLIC_API_URL=http://192.168.1.97:8000  # Your local IP
```

### Database Setup (Supabase)

1. Create project at [supabase.com](https://supabase.com)
2. Get connection string from Settings → Database
3. Update `DATABASE_URL` in `backend/.env`
4. Run `python3 backend/init_db.py` to create tables

## 📁 Project Structure

```
ScanToActionAI-SCANX/
├── app/
│   └── frontend/          # Next.js web app
│       ├── app/
│       │   ├── components/  # React components
│       │   ├── lib/         # API client
│       │   └── page.tsx     # Routes
│       └── package.json
├── backend/
│   ├── api/               # FastAPI routes
│   │   └── main.py        # Main API server
│   ├── vision/            # Vision engine
│   ├── planner/           # Planning engine
│   ├── executor/          # Execution engine
│   ├── medication/        # Drug interaction checker
│   ├── nutrition/         # Diet advisor
│   ├── memory/            # Storage & logging
│   └── requirements.txt
├── mobile/                # React Native (Expo)
│   ├── screens/
│   ├── lib/
│   └── App.tsx
└── README.md
```

## 🏆 Unique Features

### 1. Multi-Prescription Drug Interaction Checker
- Scan multiple prescriptions → Check interactions → Get warnings

### 2. Diet & Nutrition Portal
- Condition-based diet recommendations
- Food-medication interaction checking
- AI-generated meal plans

### 3. Medical Form Automation
- Scan forms → Auto-fill → Execute actions

## ⚠️ Important Notes

- **HIPAA Compliance**: This MVP is NOT HIPAA-compliant. See `HIPAA_NOTES.md` for production requirements.
- **Security**: Sensitive data is redacted, but full compliance needs additional work.
- **Costs**: LLM API calls are the main cost (~$0.01-0.08 per scan).

## 📝 License

MIT
