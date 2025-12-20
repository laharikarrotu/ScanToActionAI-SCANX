# Next Steps TODO - Speed & Accuracy Improvements

## Priority 1: High Impact, Easy Wins

### ✅ 1. Combine Vision + Planning API Calls
**Goal**: Reduce 2 API calls → 1 call (50% cost/time savings)

**What to do**:
- Modify Gemini prompts to do both vision analysis AND planning in one request
- Create combined prompt that extracts UI schema AND generates action plan
- Update `analyze-and-execute` endpoint to use combined call

**Files to modify**:
- `backend/vision/gemini_detector.py` - Add combined analysis method
- `backend/planner/gemini_planner.py` - Integrate with vision
- `backend/api/main.py` - Use combined call instead of separate calls

**Expected impact**: 50% cost reduction, 2x faster

---

### ✅ 2. Implement Tiered Model Strategy
**Goal**: Use cheaper models for simple tasks (10x cost savings)

**What to do**:
- Detect task complexity (simple vs complex)
- Use Gemini Flash for: prescription extraction, simple OCR, basic queries
- Use Gemini Pro for: complex reasoning, multi-step planning, form automation

**Files to modify**:
- `backend/medication/prescription_extractor.py` - Add Flash option
- `backend/vision/gemini_detector.py` - Add model selection logic
- `backend/api/config.py` - Add model selection settings

**Expected impact**: 70-80% cost reduction for simple tasks

---

### ✅ 3. Enhance OCR Preprocessing
**Goal**: Better text extraction before expensive API calls

**What to do**:
- Improve image enhancement (contrast, sharpening, denoising)
- Use OCR to extract text and include in prompts (reduce API token usage)
- Skip API calls for simple text-only documents

**Files to modify**:
- `backend/vision/ocr_preprocessor.py` - Enhance image processing
- `backend/vision/ui_detector.py` - Use OCR text in prompts
- `backend/medication/prescription_extractor.py` - Use OCR for simple extractions

**Expected impact**: 20-30% faster, better accuracy for text-heavy docs

---

## Priority 2: Medium Impact, Moderate Effort

### ✅ 4. Add Response Streaming
**Goal**: Show partial results immediately (better UX)

**What to do**:
- Implement streaming for Gemini API calls
- Stream vision results as they come
- Show progress in real-time on frontend

**Files to modify**:
- `backend/vision/gemini_detector.py` - Add streaming support
- `backend/api/main.py` - Return streaming responses
- `app/frontend/app/components/ScanPage.tsx` - Handle streaming updates

**Expected impact**: Better perceived performance, instant feedback

---

### ✅ 5. Improve Medical Accuracy
**Goal**: Better accuracy for prescriptions and drug names

**What to do**:
- Create medical-specific prompts with drug name databases
- Add medical terminology validation
- Use structured output formats for prescriptions

**Files to modify**:
- `backend/medication/prescription_extractor.py` - Enhanced medical prompts
- `backend/medication/interaction_checker.py` - Better drug name matching
- Create `backend/medication/drug_database.py` - Drug name lookup

**Expected impact**: 10-20% accuracy improvement

---

### ✅ 6. Add Batch Processing
**Goal**: Process multiple prescriptions in one API call

**What to do**:
- Batch multiple prescription images in single Gemini call
- Extract all medications at once
- More efficient for interaction checking

**Files to modify**:
- `backend/medication/prescription_extractor.py` - Add batch extraction
- `backend/api/main.py` - Batch processing endpoint

**Expected impact**: 30-40% faster for multi-prescription checks

---

## Priority 3: Advanced Optimizations

### ✅ 7. Implement Smart Routing
**Goal**: Skip unnecessary API calls

**What to do**:
- Detect document type before API calls
- Use OCR-only for simple text extraction
- Skip vision for known prescription formats

**Files to modify**:
- `backend/vision/image_quality.py` - Add format detection
- `backend/api/main.py` - Smart routing logic

**Expected impact**: 20-30% fewer API calls

---

### ✅ 8. Add Local Model Fallback
**Goal**: Free alternative when API fails

**What to do**:
- Integrate Ollama/Llama for simple tasks
- Use as fallback when API is down/expensive
- Local OCR for text extraction

**Files to modify**:
- Create `backend/vision/local_model.py` - Ollama integration
- `backend/api/main.py` - Fallback logic

**Expected impact**: Free option, but slower (5-10s)

---

## Implementation Order

1. **Week 1**: Combine API calls (#1) + Tiered models (#2)
2. **Week 2**: Enhanced OCR (#3) + Medical accuracy (#5)
3. **Week 3**: Response streaming (#4) + Batch processing (#6)
4. **Week 4**: Smart routing (#7) + Local fallback (#8)

---

## Quick Wins (Do First)

1. ✅ **Combine API calls** - Biggest impact, relatively easy
2. ✅ **Tiered models** - Huge cost savings, simple to implement
3. ✅ **Enhanced OCR** - Better accuracy, already have infrastructure

---

## Expected Overall Impact

- **Cost**: 60-80% reduction (from $0.10 → $0.02-0.04 per request)
- **Speed**: 2-3x faster (from 3-5s → 1-2s uncached, 0.1s cached)
- **Accuracy**: 10-20% improvement (better OCR + medical prompts)

