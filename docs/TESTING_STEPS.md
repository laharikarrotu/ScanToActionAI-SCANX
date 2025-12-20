# Testing Steps for 3 APIs

## 1. Main API: `/analyze-and-execute`

**Test Steps:**
1. Go to http://localhost:3000
2. Upload any image (prescription, form, document)
3. Enter intent: "extract medication info" or "fill this form"
4. Click "Analyze & Execute"
5. ✅ Should show: Detected elements + Action plan + Execution results

**Expected Result:**
- Vision detects 10+ elements
- Planner creates 3+ action steps
- Executor performs actions or returns data

---

## 2. Drug Interactions API: `/check-prescription-interactions`

**Test Steps:**
1. Go to http://localhost:3000/interactions
2. Upload 2-3 prescription images
3. Enter allergies (optional): "penicillin, aspirin"
4. Click "Check Interactions"
5. ✅ Should show: Color-coded warnings (major/moderate/minor)

**Expected Result:**
- Extracts medications from all prescriptions
- Checks drug-drug interactions
- Checks drug-allergy conflicts
- Shows severity levels

---

## 3. Diet Portal APIs: `/get-diet-recommendations`, `/check-food-compatibility`, `/generate-meal-plan`

**Test Steps:**
1. Go to http://localhost:3000/diet
2. **Tab 1 - Recommendations:**
   - Enter condition: "diabetes"
   - Enter medications: "metformin"
   - Click "Get Recommendations"
   - ✅ Shows diet recommendations

3. **Tab 2 - Food Check:**
   - Upload food image
   - Enter condition: "diabetes"
   - Click "Check Compatibility"
   - ✅ Shows if food is safe/unsafe

4. **Tab 3 - Meal Plan:**
   - Enter condition: "hypertension"
   - Click "Generate Meal Plan"
   - ✅ Shows 7-day meal plan

**Expected Result:**
- All 3 tabs work independently
- Returns structured recommendations
- Handles multiple conditions

---

## Quick Test Commands

```bash
# Test backend health
curl http://localhost:8000/health

# Test main API (requires image file)
curl -X POST http://localhost:8000/analyze-and-execute \
  -F "file=@test_image.jpg" \
  -F "intent=extract info"

# Test drug interactions (requires prescription images)
curl -X POST http://localhost:8000/check-prescription-interactions \
  -F "files=@prescription1.jpg" \
  -F "files=@prescription2.jpg" \
  -F "allergies=penicillin"

# Test diet recommendations
curl -X POST http://localhost:8000/get-diet-recommendations \
  -F "condition=diabetes" \
  -F "medications=metformin"
```

