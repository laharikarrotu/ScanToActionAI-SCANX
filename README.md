# HealthScan 🏥

> **Vision-Grounded AI Healthcare Assistant** - Extract prescriptions, check drug interactions, and get personalized diet recommendations from medical documents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)](https://fastapi.tiangolo.com/)

## 🎯 What is HealthScan?

HealthScan is an AI-powered healthcare assistant that uses computer vision and multimodal language models to help patients understand their medications and health information. Simply take a photo of a prescription, medical form, or insurance card, and HealthScan:

- ✅ **Extracts prescription details** (medication name, dosage, frequency, instructions)
- ✅ **Checks for drug-drug interactions** across multiple prescriptions
- ✅ **Identifies potential allergies** and contraindications
- ✅ **Provides personalized diet recommendations** based on medical conditions
- ✅ **Generates meal plans** tailored to specific health needs

### 🚨 Important Medical Disclaimer

**⚠️ HealthScan is NOT a replacement for professional medical advice.**

This tool is designed to assist patients in understanding their medications and health information. It should be used as a supplementary resource only. Always consult with qualified healthcare professionals (doctors, pharmacists, registered dietitians) before making any medical decisions, changing medications, or altering your diet based on HealthScan's recommendations.

**HealthScan does not:**
- Diagnose medical conditions
- Prescribe medications
- Replace professional medical consultation
- Guarantee accuracy of extracted information

**For medical emergencies, call 911 or your local emergency services immediately.**

## 🏗️ Architecture

HealthScan uses a **three-layer architecture** that separates concerns for scalability and maintainability:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                       │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │  Next.js Web │  │ React Native │                   │
│  │   (Web App)  │  │  (Mobile App)│                   │
│  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
                        ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────┐
│                    Backend Layer                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │         FastAPI Server (Python)                   │  │
│  │  - Prescription Extraction                        │  │
│  │  - Drug Interaction Checking                      │  │
│  │  - Diet Recommendations                           │  │
│  │  - Form Automation                                │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│                  Core Engines Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Vision     │  │   Planner    │  │   Executor   │ │
│  │   Engine     │  │   Engine     │  │   Engine     │ │
│  │              │  │              │  │              │ │
│  │ Analyzes     │  │ Creates      │  │ Automates    │ │
│  │ images &     │  │ action       │  │ browser      │ │
│  │ extracts UI  │  │ plans        │  │ interactions │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Core Engines Explained

#### 1. **Vision Engine** (`backend/vision/`)
- **Purpose**: Analyzes medical document images to detect UI elements and extract text
- **Technology**: Multimodal LLMs (Gemini Pro 1.5, GPT-4o) + OCR preprocessing
- **Output**: Structured UI schema with detected elements (medications, dosages, labels, etc.)
- **Files**: `ui_detector.py`, `gemini_detector.py`, `combined_analyzer.py`, `ocr_preprocessor.py`

#### 2. **Planner Engine** (`backend/planner/`)
- **Purpose**: Creates step-by-step action plans based on user intent and detected UI elements
- **Technology**: LLM-based planning (Gemini Pro, GPT-4o) with confidence-based fallbacks
- **Output**: Action plan with steps (fill, click, read, navigate, etc.)
- **Files**: `agent_planner.py`, `gemini_planner.py`

#### 3. **Executor Engine** (`backend/executor/`)
- **Purpose**: Automates browser interactions for form filling and data extraction
- **Technology**: Playwright for cross-browser automation
- **Output**: Execution results with screenshots and logs
- **Files**: `browser_executor.py`

### Data Flow

```
User Uploads Image
       ↓
Vision Engine → Extracts UI Elements & Text
       ↓
Planner Engine → Creates Action Plan
       ↓
Executor Engine → Performs Actions (if needed)
       ↓
Prescription Extractor → Parses Medication Data
       ↓
Interaction Checker → Validates Safety
       ↓
Diet Advisor → Provides Recommendations
       ↓
User Receives Results
```

## 📊 Example Outputs

### Prescription Extraction Example

**Input**: Photo of prescription bottle

**Output**:
```json
{
  "medication_name": "Metformin",
  "dosage": "500mg",
  "frequency": "Twice daily",
  "quantity": "60 tablets",
  "refills": "3",
  "instructions": "Take with meals",
  "prescriber": "Dr. Smith",
  "date": "2024-01-15"
}
```

### Drug Interaction Check Example

**Input**: Multiple prescriptions

**Output**:
```json
{
  "warnings": [
    {
      "severity": "moderate",
      "medication1": "Warfarin",
      "medication2": "Aspirin",
      "description": "Increased risk of bleeding",
      "recommendation": "Monitor INR closely. Consult your doctor before taking both medications together."
    }
  ],
  "allergy_warnings": [
    {
      "severity": "major",
      "medication": "Penicillin",
      "allergy": "Penicillin",
      "description": "Patient has known allergy to this medication",
      "recommendation": "Do not take this medication. Contact your doctor immediately."
    }
  ]
}
```

### Diet Recommendation Example

**Input**: Medical condition (e.g., "Type 2 Diabetes")

**Output**:
```json
{
  "foods_to_eat": [
    "Whole grains (brown rice, quinoa)",
    "Leafy greens (spinach, kale)",
    "Lean proteins (chicken, fish)",
    "Low-glycemic fruits (berries, apples)"
  ],
  "foods_to_avoid": [
    "Refined sugars",
    "White bread and pasta",
    "Sugary drinks",
    "Processed foods"
  ],
  "nutritional_focus": "Blood sugar control, fiber intake, portion management"
}
```

## 🔬 How Drug Interaction Checking Works

### Data Sources

HealthScan uses multiple data sources for comprehensive interaction checking:

1. **RxNav/RxNorm API** (Free, no API key required)
   - Drug name normalization
   - Standardized medication identifiers
   - Cross-references between brand and generic names

2. **Common Interactions Database** (Built-in)
   - Curated list of well-known drug interactions
   - Includes severity levels (major, moderate, minor)
   - Examples: Warfarin + Aspirin, Metformin + Alcohol

3. **Future Integration** (Planned)
   - DrugBank API (requires API key)
   - FDA Adverse Event Reporting System (FAERS)
   - Clinical drug interaction databases

### Interaction Checking Process

```
1. Normalize Medication Names
   ↓
2. Check Pairwise Interactions
   ↓
3. Check Against Allergies
   ↓
4. Generate Warnings with Severity Levels
   ↓
5. Provide Recommendations
```

**Severity Levels:**
- **Major**: Life-threatening interactions requiring immediate medical attention
- **Moderate**: Significant interactions requiring monitoring or dose adjustment
- **Minor**: Mild interactions with minimal clinical significance

## 🛠️ Tech Stack

### Frontend
- **Web**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Mobile**: React Native (Expo), TypeScript
- **UI Components**: shadcn/ui

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Server**: Uvicorn with ASGI
- **Database**: PostgreSQL (Supabase)
- **Caching**: Redis (optional, falls back to in-memory)
- **Task Queue**: Celery (optional, for background processing)

### AI/ML
- **Vision Models**: Gemini Pro 1.5, GPT-4o
- **Planning Models**: Gemini Pro 1.5, GPT-4o
- **OCR**: Tesseract OCR with preprocessing
- **Image Processing**: OpenCV, PIL/Pillow

### Infrastructure
- **Monitoring**: Prometheus metrics, Sentry error tracking
- **Security**: JWT authentication, PII redaction, image encryption
- **Automation**: Playwright for browser automation

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL (or Supabase account)
- Tesseract OCR (for image preprocessing)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY (or GEMINI_API_KEY)
# - DATABASE_URL (Supabase connection string)
# - JWT_SECRET

# Initialize database (if using Supabase)
python init_db.py

# Run the server
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Prometheus Metrics: `http://localhost:8000/metrics`

### Frontend Setup

```bash
# Navigate to frontend directory
cd app/frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

The web app will be available at `http://localhost:3000`

### Mobile Setup

```bash
# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# Start Expo development server
npm start

# Scan QR code with Expo Go app (iOS/Android)
```

## 📁 Project Structure

```
HealthScan/
├── app/
│   └── frontend/          # Next.js web application
│       ├── app/           # Next.js 15 app directory
│       ├── components/   # React components
│       └── lib/           # API client, types
├── backend/               # FastAPI backend
│   ├── api/              # API endpoints
│   ├── core/             # Core utilities (logging, encryption, monitoring)
│   ├── vision/           # Vision Engine
│   ├── planner/          # Planner Engine
│   ├── executor/         # Executor Engine
│   ├── medication/       # Prescription extraction & interaction checking
│   ├── nutrition/        # Diet recommendations
│   └── workers/          # Celery background tasks
├── mobile/                # React Native mobile app
├── tests/                 # E2E tests
└── docs/                  # Documentation
```

## 🔌 API Endpoints

### Core Endpoints

- `POST /extract-prescription` - Extract prescription details from image
- `POST /check-prescription-interactions` - Check for drug interactions
- `POST /get-diet-recommendations` - Get diet recommendations for condition
- `POST /analyze-and-execute` - Full pipeline (vision + planning + execution)
- `GET /metrics` - Prometheus metrics endpoint

### Authentication

- `POST /login` - Get JWT token
- `GET /protected` - Protected endpoint example

See [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md) for complete API documentation.

## 🧪 Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Run E2E tests
cd tests/e2e
pytest test_full_pipeline.py

# Test full flow
python test_full_flow.py
```

## 📸 Screenshots & Demos

> **Note**: Screenshots and demo videos will be added soon. Check back for:
> - Web app interface screenshots
> - Mobile app screenshots
> - Example prescription extraction results
> - Drug interaction warning displays
> - Diet recommendation interface

## 🔒 Security & Privacy

### HIPAA Compliance

**⚠️ Important**: HealthScan is currently an **MVP** and is **NOT HIPAA-compliant** for production use with real patient data.

See [docs/HIPAA_COMPLIANCE_ROADMAP.md](docs/HIPAA_COMPLIANCE_ROADMAP.md) for the compliance roadmap.

### Current Security Features

- ✅ PII (Personally Identifiable Information) redaction before LLM processing
- ✅ Image encryption at rest (optional)
- ✅ Audit logging for PHI access
- ✅ JWT authentication
- ✅ Rate limiting
- ✅ Input validation and sanitization

### Planned Security Enhancements

- 🔄 End-to-end encryption
- 🔄 BAA (Business Associate Agreement) with cloud providers
- 🔄 SOC 2 compliance
- 🔄 Regular security audits

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines (coming soon) before submitting pull requests.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o API
- Google for Gemini Pro 1.5 API
- Supabase for PostgreSQL hosting
- Playwright for browser automation
- Tesseract OCR for text extraction

## 📧 Contact

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Remember**: HealthScan is a tool to assist patients, not replace professional medical advice. Always consult with healthcare professionals for medical decisions.
