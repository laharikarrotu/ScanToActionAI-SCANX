# HealthScan API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://your-api-domain.com
```

## Authentication

Most endpoints require JWT authentication. Get a token via `/login`:

```bash
POST /login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Use the token in subsequent requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### 1. Extract Prescription

Extract medication details from a prescription image.

**Endpoint**: `POST /extract-prescription`

**Request**:
```bash
Content-Type: multipart/form-data

file: <image file>
stream: true (optional, for real-time progress)
```

**Response**:
```json
{
  "status": "success",
  "prescription_info": {
    "medication_name": "Metformin",
    "dosage": "500mg",
    "frequency": "Twice daily",
    "quantity": "60 tablets",
    "refills": "3",
    "instructions": "Take with meals",
    "prescriber": "Dr. Smith",
    "date": "2024-01-15"
  },
  "message": "Prescription extracted successfully",
  "cached": false
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/extract-prescription \
  -F "file=@prescription.jpg" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Check Drug Interactions

Check for interactions between multiple medications.

**Endpoint**: `POST /check-prescription-interactions`

**Request**:
```bash
Content-Type: multipart/form-data

files: <image files> (multiple)
allergies: "Penicillin, Sulfa" (optional, comma-separated)
```

**Response**:
```json
{
  "status": "success",
  "medications": [
    {
      "name": "Warfarin",
      "dosage": "5mg",
      "frequency": "Once daily"
    },
    {
      "name": "Aspirin",
      "dosage": "81mg",
      "frequency": "Once daily"
    }
  ],
  "warnings": [
    {
      "severity": "moderate",
      "medication1": "Warfarin",
      "medication2": "Aspirin",
      "description": "Increased risk of bleeding when taken together",
      "recommendation": "Monitor INR closely. Consult your doctor before taking both medications together."
    }
  ],
  "allergy_warnings": []
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/check-prescription-interactions \
  -F "files=@prescription1.jpg" \
  -F "files=@prescription2.jpg" \
  -F "allergies=Penicillin" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Get Diet Recommendations

Get personalized diet recommendations for a medical condition.

**Endpoint**: `POST /get-diet-recommendations`

**Request**:
```bash
Content-Type: application/x-www-form-urlencoded

condition: "Type 2 Diabetes"
medications: "Metformin, Insulin" (optional)
```

**Response**:
```json
{
  "status": "success",
  "recommendation": {
    "condition": "Type 2 Diabetes",
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
    "nutritional_focus": "Blood sugar control, fiber intake, portion management",
    "warnings": [
      "Monitor blood sugar levels regularly",
      "Consult with a registered dietitian for personalized meal planning"
    ]
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/get-diet-recommendations \
  -d "condition=Type 2 Diabetes" \
  -d "medications=Metformin" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Analyze and Execute

Full pipeline: vision analysis + planning + execution (for form automation).

**Endpoint**: `POST /analyze-and-execute`

**Request**:
```bash
Content-Type: multipart/form-data

file: <image file>
intent: "Fill this medical form"
context: "{"patient_name": "John Doe"}" (optional, JSON string)
verify_only: true (optional, for HITL verification)
```

**Response**:
```json
{
  "status": "success",
  "ui_schema": {
    "page_type": "medical_form",
    "elements": [
      {
        "id": "name_field",
        "type": "input",
        "label": "Patient Name",
        "value": null
      }
    ]
  },
  "plan": {
    "task": "Fill medical form",
    "steps": [
      {
        "step": 1,
        "action": "fill",
        "target": "name_field",
        "value": "John Doe",
        "description": "Fill patient name field"
      }
    ]
  },
  "execution": {
    "status": "success",
    "message": "Form filled successfully",
    "screenshot_path": "/screenshots/..."
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/analyze-and-execute \
  -F "file=@form.jpg" \
  -F "intent=Fill this medical form" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Prometheus Metrics

Get Prometheus metrics for monitoring.

**Endpoint**: `GET /metrics`

**Response**: Prometheus text format

**Example**:
```bash
curl http://localhost:8000/metrics
```

**Available Metrics**:
- `healthscan_http_requests_total` - HTTP request counts
- `healthscan_http_request_duration_seconds` - Request latencies
- `healthscan_llm_api_calls_total` - LLM API call counts
- `healthscan_llm_api_duration_seconds` - LLM API call durations
- `healthscan_vision_analyses_total` - Vision analysis counts
- `healthscan_prescription_extractions_total` - Prescription extraction counts
- `healthscan_browser_executions_total` - Browser execution counts
- `healthscan_cache_hits_total` - Cache hit counts
- `healthscan_cache_misses_total` - Cache miss counts

## Error Responses

All endpoints return errors in this format:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error_type": "ErrorClassName"
}
```

**Common Status Codes**:
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Rate Limiting

Default rate limit: **20 requests per minute per IP address**

Rate limit headers:
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 1640995200
```

## Streaming Responses

Some endpoints support Server-Sent Events (SSE) for real-time progress:

```bash
POST /extract-prescription?stream=true
```

Response format:
```
data: {"step": "preprocessing", "progress": 25, "message": "Processing image..."}

data: {"step": "extraction", "progress": 50, "message": "Extracting prescription details..."}

data: {"step": "complete", "progress": 100, "prescription_info": {...}}
```

## Data Sources

### Drug Interactions

- **RxNav/RxNorm API**: Drug name normalization (free, no API key)
- **Common Interactions Database**: Built-in curated interactions
- **Future**: DrugBank API, FAERS database

### Diet Recommendations

- **LLM-Based**: Uses Gemini Pro 1.5 or GPT-4o with medical knowledge
- **Condition-Specific**: Tailored to medical conditions and medications
- **Evidence-Based**: Based on medical literature and guidelines

## SDK Examples

### Python

```python
import requests

# Extract prescription
with open('prescription.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/extract-prescription',
        files={'file': f},
        headers={'Authorization': f'Bearer {token}'}
    )
    prescription = response.json()['prescription_info']
    print(f"Medication: {prescription['medication_name']}")
```

### JavaScript/TypeScript

```typescript
import { extractPrescription } from './lib/api';

const file = document.querySelector('input[type="file"]').files[0];
const result = await extractPrescription(file, (progress) => {
  console.log(`Progress: ${progress.progress}% - ${progress.message}`);
});

console.log(result.prescription_info);
```

## WebSocket Support (Future)

WebSocket endpoints for real-time updates are planned for future releases.

