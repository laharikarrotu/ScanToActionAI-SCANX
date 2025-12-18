# HealthScan

HealthScan is a vision-grounded AI agent designed to assist with healthcare documentation and decision-making. The system analyzes medical forms, prescriptions, and insurance cards through computer vision, then provides actionable insights or automates form-filling tasks. Built with modern AI models and browser automation, it aims to reduce the administrative burden in healthcare interactions.

## Overview

The project emerged from recognizing that healthcare paperwork often creates friction between patients and providers. HealthScan addresses this by combining multimodal language models with automated execution capabilities. Users can capture images of medical documents, and the system extracts relevant information, checks for potential issues (such as drug interactions), and either fills forms automatically or provides structured recommendations.

The architecture follows a modular design, separating vision analysis, task planning, and execution into distinct engines. This separation allows for independent optimization and makes the system more maintainable as it scales.

## Architecture

The system is organized into several layers:

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

### Execution Flow

The system processes requests through a pipeline:

1. **Input Capture**: The frontend captures an image along with user intent (e.g., "fill this form" or "check interactions")
2. **Vision Analysis**: The Vision Engine uses multimodal LLMs to extract UI elements, text, and structured data from the image
3. **Task Planning**: The Planner Engine generates a step-by-step action plan based on the extracted schema and user intent
4. **Execution**: The Executor Engine uses Playwright to perform browser automation or returns structured recommendations
5. **Logging**: All events are logged to the memory layer for audit trails and future reference
6. **Response**: Results are returned to the frontend for display

## Technology Stack

**Frontend:**
- Next.js 15 with React and TypeScript for the web interface
- Tailwind CSS for styling
- Expo (React Native) for mobile applications

**Backend:**
- FastAPI (Python) serving as the async API framework
- GPT-4o, Claude, and Gemini for vision analysis and reasoning
- Playwright for browser automation
- PostgreSQL via Supabase for persistent storage
- SQLAlchemy as the ORM layer

**Infrastructure:**
- Vercel for frontend hosting
- Railway or Render for backend deployment
- Supabase for database and optional authentication services

## Data Structures and Algorithms

The implementation leverages several fundamental data structures:

- **Lists and Arrays**: Used for managing medication lists, action step sequences, and UI element collections
- **Dictionaries and Hash Maps**: Employed for UI schema representations, interaction databases, and configuration management
- **Trees**: JSON structures handle nested data hierarchies in action plans and UI schemas
- **Graphs**: Medication interaction networks are implicitly modeled through pairwise relationship checks
- **Sets**: Utilized for domain allowlisting and pattern matching in sensitive data redaction
- **Queues**: Task execution queues are prepared for future integration with Celery or Redis

Algorithmic approaches include graph traversal for drug interaction checking, string matching for data redaction, search algorithms for element selector matching in Playwright, async/await patterns for concurrent LLM calls, and state machine patterns for managing execution flow.

## System Design Considerations

The architecture implements several established patterns:

**Currently Implemented:**
- Microservices architecture with separate modules for vision, planning, and execution
- API Gateway pattern using FastAPI as the single entry point
- Asynchronous processing for non-blocking I/O during LLM calls
- Relational database design with schemas for users, sessions, and audit logs
- Comprehensive error handling with graceful degradation
- CORS and security measures including multi-origin support and JWT authentication
- Logging and observability through event logging and audit trails

**Planned Enhancements:**
- Message queues (Redis/Celery) for background task processing
- Caching layer for LLM responses and UI schemas
- Load balancing across multiple backend instances
- Per-user rate limiting
- Circuit breakers for LLM API failure handling
- Database sharding for storage scaling
- CDN integration for static asset delivery
- Monitoring infrastructure with Prometheus and Grafana

## Getting Started

### Prerequisites

The system requires:
- macOS, Linux, or Windows
- Node.js 18 or higher (installation via nvm is recommended)
- Python 3.11 or higher
- Git
- 16GB RAM recommended (Playwright browser automation is memory-intensive)

API keys and services needed:
- OpenAI API key for GPT-4o vision capabilities
- Supabase project for database hosting
- Optional: Anthropic API key for Claude, Google API key for Gemini

### Installation

**1. Clone the repository:**
```bash
git clone <repository-url>
cd ScanToActionAI-SCANX
```

**2. Frontend setup:**
```bash
cd app/frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```
The frontend will be available at `http://localhost:3000`.

**3. Backend setup:**
```bash
cd backend
pip3 install -r requirements.txt
playwright install chromium
```

Create a `.env` file in the backend directory:
```bash
cat > .env << EOF
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:password@host:port/dbname
FRONTEND_URL=http://localhost:3000
JWT_SECRET=your-secret-key-here
ALLOWED_DOMAINS=example.com
EOF
```

Initialize the database:
```bash
python3 init_db.py
```

Start the server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**4. Mobile setup (optional):**
```bash
cd mobile
npm install
echo "EXPO_PUBLIC_API_URL=http://YOUR_IP:8000" > .env
npx expo start
```

### Environment Configuration

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
EXPO_PUBLIC_API_URL=http://192.168.1.97:8000
```

### Database Configuration

For Supabase setup:
1. Create a project at [supabase.com](https://supabase.com)
2. Retrieve the connection string from Settings → Database
3. Update the `DATABASE_URL` in `backend/.env`
4. Run `python3 backend/init_db.py` to initialize the database schema

## Project Structure

```
ScanToActionAI-SCANX/
├── app/
│   └── frontend/          # Next.js web application
│       ├── app/
│       │   ├── components/  # React components
│       │   ├── lib/         # API client utilities
│       │   └── page.tsx     # Application routes
│       └── package.json
├── backend/
│   ├── api/               # FastAPI route handlers
│   │   └── main.py        # Main API server
│   ├── vision/            # Vision analysis engine
│   ├── planner/           # Task planning engine
│   ├── executor/          # Browser automation engine
│   ├── medication/        # Drug interaction checking module
│   ├── nutrition/         # Diet and nutrition advisory module
│   ├── memory/            # Storage and logging layer
│   └── requirements.txt
├── mobile/                # React Native application (Expo)
│   ├── screens/
│   ├── lib/
│   └── App.tsx
└── README.md
```

## Key Features

### Multi-Prescription Drug Interaction Checker

The system can process multiple prescription images simultaneously, extract medication information, and check for potential drug-drug and drug-allergy interactions. This feature addresses a common safety concern in polypharmacy scenarios.

### Diet and Nutrition Portal

A specialized module provides condition-based diet recommendations, checks for food-medication interactions, and generates AI-powered meal plans tailored to specific medical conditions.

### Medical Form Automation

The core functionality enables automated form filling by analyzing form structure, extracting relevant information, and executing browser-based actions to complete documentation tasks.

## Important Considerations

**HIPAA Compliance**: The current implementation is an MVP and is not HIPAA-compliant. Production deployment would require additional security measures, encryption, access controls, and compliance auditing. See the documentation in `docs/HIPAA_NOTES.md` for detailed requirements.

**Security**: While sensitive data redaction is implemented, full production-grade security requires additional hardening, regular security audits, and compliance certifications.

**Cost Considerations**: The primary operational cost comes from LLM API calls, typically ranging from $0.01 to $0.08 per scan depending on image complexity and model selection.

## License

MIT License
