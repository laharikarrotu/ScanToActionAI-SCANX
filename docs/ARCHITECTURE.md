# HealthScan Architecture Documentation

## Overview

HealthScan uses a **three-layer architecture** that separates concerns for scalability, maintainability, and independent optimization of each component.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌────────────────────┐          ┌────────────────────┐        │
│  │   Next.js Web App   │          │  React Native App   │        │
│  │   (TypeScript)      │          │   (Expo/TypeScript) │        │
│  │                     │          │                     │        │
│  │  - Scan Page        │          │  - Scan Screen      │        │
│  │  - Interactions     │          │  - Camera Capture   │        │
│  │  - Diet Portal      │          │  - Results Display  │        │
│  └────────────────────┘          └────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              FastAPI Server (Python)                       │  │
│  │                                                            │  │
│  │  Endpoints:                                                │  │
│  │  - POST /extract-prescription                              │  │
│  │  - POST /check-prescription-interactions                  │  │
│  │  - POST /get-diet-recommendations                          │  │
│  │  - POST /analyze-and-execute                               │  │
│  │  - GET /metrics (Prometheus)                              │  │
│  │                                                            │  │
│  │  Middleware:                                               │  │
│  │  - CORS                                                    │  │
│  │  - Request Logging                                         │  │
│  │  - Performance Tracking                                    │  │
│  │  - Rate Limiting                                           │  │
│  │  - Error Handling                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      CORE ENGINES LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Vision     │  │   Planner    │  │   Executor   │          │
│  │   Engine     │  │   Engine     │  │   Engine     │          │
│  │              │  │              │  │              │          │
│  │ Input:       │  │ Input:       │  │ Input:       │          │
│  │ - Image      │  │ - UI Schema  │  │ - Action Plan│          │
│  │ - Hint       │  │ - User Intent│  │ - UI Schema  │          │
│  │              │  │ - Context    │  │ - Start URL  │          │
│  │ Output:      │  │              │  │              │          │
│  │ - UI Schema  │  │ Output:      │  │ Output:      │          │
│  │ - Elements   │  │ - Action Plan│  │ - Results    │          │
│  │ - Text       │  │ - Steps      │  │ - Screenshots│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Supporting Modules                             │  │
│  │  - Prescription Extractor                                │  │
│  │  - Interaction Checker                                   │  │
│  │  - Diet Advisor                                          │  │
│  │  - OCR Preprocessor                                      │  │
│  │  - PDF Processor                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │   Celery     │          │
│  │  (Supabase)  │  │   (Cache)    │  │  (Workers)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Prometheus  │  │    Sentry    │  │   Playwright │          │
│  │  (Metrics)   │  │  (Errors)    │  │  (Browser)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Core Engines Deep Dive

### 1. Vision Engine

**Location**: `backend/vision/`

**Purpose**: Analyzes medical document images to extract structured information.

**Components**:
- `ui_detector.py` - Main vision engine using GPT-4o
- `gemini_detector.py` - Alternative engine using Gemini Pro 1.5
- `combined_analyzer.py` - Combined vision + planning in one call (optimization)
- `ocr_preprocessor.py` - Image preprocessing and OCR text extraction
- `image_quality.py` - Image quality checks (blur, resolution, lighting)
- `pdf_processor.py` - Multi-page PDF to image conversion

**Process**:
```
Image Input
    ↓
OCR Preprocessing (enhance quality)
    ↓
Text Extraction (Tesseract OCR)
    ↓
Document Type Identification (LLM)
    ↓
UI Element Detection (Multimodal LLM)
    ↓
Structured UI Schema Output
```

**Output Format**:
```python
UISchema(
    page_type: str,  # "prescription", "medical_form", etc.
    url_hint: Optional[str],
    elements: List[UIElement]  # Detected UI elements
)
```

### 2. Planner Engine

**Location**: `backend/planner/`

**Purpose**: Creates actionable step-by-step plans based on user intent and detected UI elements.

**Components**:
- `agent_planner.py` - Main planner using GPT-4o
- `gemini_planner.py` - Alternative planner using Gemini Pro 1.5

**Process**:
```
User Intent + UI Schema
    ↓
LLM-Based Planning (with context)
    ↓
Confidence Scoring
    ↓
Fallback Strategy (if low confidence)
    ↓
Action Plan Output
```

**Output Format**:
```python
ActionPlan(
    task: str,
    steps: List[ActionStep],  # Ordered steps to execute
    estimated_time: int
)
```

**Fallback Strategy** (3-tier):
1. **Primary**: LLM-generated plan
2. **Secondary**: Heuristic-based plan from UI elements
3. **Tertiary**: Generic "read document" plan

### 3. Executor Engine

**Location**: `backend/executor/`

**Purpose**: Automates browser interactions to fill forms or extract data from web pages.

**Components**:
- `browser_executor.py` - Playwright-based browser automation

**Process**:
```
Action Plan + UI Schema
    ↓
Initialize Browser (Playwright)
    ↓
Navigate to Start URL
    ↓
Execute Steps (click, fill, select, etc.)
    ↓
Capture Screenshots
    ↓
Cleanup Resources
    ↓
Execution Results
```

**Actions Supported**:
- `click` - Click buttons, links
- `fill` - Fill input fields
- `select` - Select dropdown options
- `read` - Extract text/data
- `navigate` - Navigate to URLs
- `wait` - Wait for conditions

## Data Flow Examples

### Example 1: Prescription Extraction

```
User uploads prescription image
    ↓
Vision Engine → Detects medication name, dosage, etc.
    ↓
Prescription Extractor → Parses structured data
    ↓
Cache Result (24 hours)
    ↓
Return to user
```

### Example 2: Drug Interaction Check

```
User uploads multiple prescriptions
    ↓
Extract all medications
    ↓
Normalize drug names (RxNav API)
    ↓
Check pairwise interactions (database)
    ↓
Check against allergies
    ↓
Generate warnings with severity
    ↓
Return interaction report
```

### Example 3: Form Automation

```
User uploads form image + intent "Fill this form"
    ↓
Vision Engine → Detects form fields
    ↓
Planner Engine → Creates fill plan
    ↓
HITL Verification → User reviews/edits
    ↓
Executor Engine → Fills form in browser
    ↓
Capture results
    ↓
Return to user
```

## Scalability Features

### Caching
- **Redis** (primary) or **in-memory** (fallback)
- Cache keys: Image hash, medication combinations, queries
- TTL: 1 hour (UI schemas), 24 hours (prescriptions)

### Rate Limiting
- **Redis-based** (distributed) or **Token Bucket** (in-memory)
- Default: 20 requests/minute per IP
- Configurable per endpoint

### Background Processing
- **Celery** workers for long-running tasks
- Async task queue with Redis broker
- Task status tracking

### Monitoring
- **Prometheus** metrics endpoint (`/metrics`)
- **Sentry** error tracking
- Request/response logging
- Performance tracking

## Security Architecture

### Data Protection
- **PII Redaction**: Automatic before LLM processing
- **Image Encryption**: Optional at-rest encryption
- **Audit Logging**: PHI access tracking
- **JWT Authentication**: Secure API access

### Error Handling
- Circuit breakers for LLM APIs
- Retry with exponential backoff
- Graceful degradation
- User-friendly error messages

## Deployment Architecture

### Development
- Local PostgreSQL (or Supabase)
- In-memory cache
- Single FastAPI instance
- Next.js dev server

### Production (Recommended)
- **Frontend**: Vercel (Next.js)
- **Backend**: Railway/Render (FastAPI)
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis (Upstash/Redis Cloud)
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry

## Performance Optimizations

1. **Combined Analyzer**: Vision + Planning in 1 API call (50% faster)
2. **Caching**: Aggressive caching of LLM responses
3. **Streaming**: Server-Sent Events for real-time progress
4. **Connection Pooling**: Database connection reuse
5. **Async Processing**: Celery for background tasks

## Future Enhancements

- [ ] Vector database for semantic search
- [ ] Multi-region deployment
- [ ] CDN for static assets
- [ ] GraphQL API option
- [ ] WebSocket support for real-time updates
- [ ] Advanced caching strategies
- [ ] Database sharding

