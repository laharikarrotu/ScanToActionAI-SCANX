# Improving Medical Document Detection Accuracy

## ✅ What I Just Fixed

1. **Enhanced Prompt**: More detailed instructions for medical documents
2. **Lower Temperature**: Changed from 0.1 to 0.0 for more consistent results
3. **More Tokens**: Increased max_tokens to 4000 for detailed extraction
4. **Better Error Handling**: Added fallback prompts if first attempt fails
5. **Medical-Specific Instructions**: Focused on prescriptions, forms, insurance cards

## 🎯 Immediate Improvements (Already Applied)

### 1. Better Prompt Engineering
- More specific instructions for medical documents
- Explicitly asks for ALL text, even if small or unclear
- Focuses on prescription-specific fields (medication name, dosage, instructions)
- Requires minimum 5 elements to prevent empty results

### 2. Model Settings
- **Temperature: 0.0** (was 0.1) - More deterministic, accurate results
- **Max Tokens: 4000** (was default) - Allows detailed extraction
- **JSON Mode**: Ensures structured output

## 🚀 Additional Improvements You Can Make

### Option 1: Image Preprocessing (Recommended)
**Problem**: Blurry, dark, or rotated images reduce accuracy

**Solution**: Add image preprocessing before sending to LLM

```python
# Add to requirements.txt:
# opencv-python==4.8.1.78
# pytesseract==0.3.10

# In ui_detector.py, add preprocessing:
from PIL import Image
import io
import cv2
import numpy as np

def preprocess_image(image_data: bytes) -> bytes:
    """Enhance image quality before analysis"""
    # Convert to PIL Image
    img = Image.open(io.BytesIO(image_data))
    
    # Convert to OpenCV format
    img_array = np.array(img)
    
    # Enhance contrast
    img_array = cv2.convertScaleAbs(img_array, alpha=1.5, beta=30)
    
    # Sharpen image
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    img_array = cv2.filter2D(img_array, -1, kernel)
    
    # Convert back to bytes
    _, buffer = cv2.imencode('.jpg', img_array)
    return buffer.tobytes()
```

### Option 2: Hybrid OCR + LLM Approach
**Problem**: LLM might miss small text or numbers

**Solution**: Use OCR first, then LLM for structure

```python
# Add pytesseract for OCR
import pytesseract

def extract_text_with_ocr(image_data: bytes) -> str:
    """Extract all text using OCR"""
    img = Image.open(io.BytesIO(image_data))
    text = pytesseract.image_to_string(img)
    return text

# Then include OCR text in prompt:
ocr_text = extract_text_with_ocr(image_data)
prompt += f"\n\nOCR Extracted Text:\n{ocr_text}\n\nUse this text to help identify elements."
```

### Option 3: Multi-Step Detection
**Problem**: Single pass might miss details

**Solution**: Two-pass approach
1. First pass: Identify document type
2. Second pass: Extract details based on type

```python
# First pass - identify type
type_prompt = "What type of medical document is this? (prescription, form, insurance_card, etc.)"

# Second pass - extract based on type
if document_type == "prescription":
    prompt = prescription_specific_prompt
elif document_type == "medical_form":
    prompt = form_specific_prompt
```

### Option 4: Use Medical-Specific LLM (Advanced)
**Do you need a medical LLM?**

**Short Answer**: GPT-4o is already very good, but medical LLMs can help for:
- Medical terminology accuracy
- Drug name recognition
- Dosage interpretation
- Medical abbreviations

**Options**:
1. **Med-PaLM 2** (Google) - Medical-specific, but limited access
2. **GPT-4o with medical fine-tuning** - Use medical prompts (what we're doing)
3. **Claude 3.5 Sonnet** - Better at structured data extraction
4. **Specialized APIs**: 
   - **Nuance DAX** - Medical documentation
   - **Epic MyChart APIs** - Healthcare-specific

**Recommendation**: Start with improved prompts (already done). If accuracy is still low, try:
- Claude 3.5 Sonnet (often better at structured extraction)
- Add OCR preprocessing
- Use multi-step detection

### Option 5: Increase Image Resolution
**Problem**: Low-resolution images = poor detection

**Solution**: 
- Request higher resolution from users
- Upscale images before processing
- Use "detail": "high" in OpenAI API (already using best model)

```python
# In the API call, ensure high detail:
"image_url": {
    "url": f"data:image/jpeg;base64,{image_base64}",
    "detail": "high"  # For gpt-4o, this is automatic
}
```

### Option 6: Add Confidence Scores
**Problem**: Don't know if detection is reliable

**Solution**: Ask LLM to provide confidence scores

```python
# In prompt, add:
"Also include a 'confidence' score (0-1) for each element indicating how certain you are about the extraction."
```

## 📋 Quick Wins Checklist

- [x] Enhanced prompt with medical-specific instructions
- [x] Lower temperature (0.0) for consistency
- [x] More tokens (4000) for detailed extraction
- [x] Better error handling with fallback
- [ ] Add image preprocessing (contrast, sharpening)
- [ ] Add OCR as backup text extraction
- [ ] Try Claude 3.5 Sonnet for comparison
- [ ] Add confidence scores to results
- [ ] Implement multi-step detection
- [ ] Add image quality validation before processing

## 🔧 Testing Recommendations

1. **Test with different image qualities**:
   - High resolution prescription photos
   - Blurry/low-light images
   - Rotated images
   - Multiple prescriptions in one image

2. **Test with different document types**:
   - Prescription bottles
   - Prescription papers
   - Medical forms
   - Insurance cards

3. **Monitor detection rates**:
   - Track how many elements are detected
   - Compare before/after improvements
   - Log cases where detection fails

## 💡 Best Practices for Users

Tell users to:
1. **Take clear photos**: Good lighting, in focus
2. **Fill the frame**: Get close to the document
3. **Avoid glare**: Don't use flash on glossy surfaces
4. **Straight angle**: Hold camera parallel to document
5. **High resolution**: Use phone's highest camera setting

## 🎯 Expected Results After Improvements

**Before**: 0-2 elements detected
**After (with improvements)**: 5-20+ elements detected

The enhanced prompt should immediately improve results. If you still get 0 elements:
1. Check image quality (might be too blurry)
2. Try a different image
3. Add OCR preprocessing
4. Consider using Claude 3.5 Sonnet

## 📞 Next Steps

1. **Test the current improvements** - The enhanced prompt should help immediately
2. **If still low accuracy**: Add image preprocessing (Option 1)
3. **If text is missed**: Add OCR (Option 2)
4. **If structured data is poor**: Try Claude 3.5 Sonnet
5. **For production**: Implement all improvements + confidence scores

