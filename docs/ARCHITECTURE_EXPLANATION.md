# 🎯 Main Purpose & Architecture: Vision → Plan → Execute

## The Core Philosophy

**"See, Think, Act"** - A three-stage AI agent that:
1. **SEES** (Vision Engine) - Understands what's in the image
2. **THINKS** (Planner Engine) - Decides what actions to take
3. **ACTS** (Executor Engine) - Performs the actions

## The Main Motto

> **"Turn any image into actionable steps, then execute them automatically"**

This system is designed to be **universal** - it should work with:
- ✅ Prescriptions
- ✅ Medical forms
- ✅ Insurance cards
- ✅ Lab results
- ✅ Appointment pages
- ✅ Any document or image you scan

## How It Works

### Stage 1: Vision Engine (SEE)
**Purpose**: Understand what's in the image

**What it does**:
- Uses GPT-4o Vision to analyze the image
- Extracts text using OCR (Tesseract)
- Identifies document type (prescription, form, card, etc.)
- Creates a structured schema of all elements found:
  - Text elements
  - Input fields
  - Buttons
  - Medication names
  - Dosages
  - Any visible information

**Output**: A structured "UI Schema" with all detected elements

### Stage 2: Planner Engine (THINK)
**Purpose**: Decide what to do with the detected elements

**What it does**:
- Takes the UI Schema + Your Intent (e.g., "fill this form", "extract medication info")
- Uses GPT-4o to create a step-by-step action plan
- Determines the right actions:
  - **Read** - Extract information
  - **Fill** - Enter data into forms
  - **Click** - Press buttons, select options
  - **Navigate** - Go to URLs

**Output**: An Action Plan with numbered steps

### Stage 3: Executor Engine (ACT)
**Purpose**: Actually perform the actions

**What it does**:
- Uses Playwright (browser automation) to:
  - Navigate to websites
  - Fill form fields
  - Click buttons
  - Extract data
- OR returns structured data if no browser automation needed

**Output**: Execution results (success/error, data extracted, screenshots)

## Why This Architecture?

### 1. **Modularity**
Each engine is independent - you can improve one without breaking others

### 2. **Flexibility**
- Works with ANY image type
- Works with ANY intent
- Can adapt to different document types

### 3. **Scalability**
- Vision can use different AI models
- Planner can use different reasoning models
- Executor can use different automation tools

### 4. **Transparency**
- You can see what was detected (Vision)
- You can see the plan (Planner)
- You can see what was executed (Executor)

## Current Limitations & Fixes

### ✅ FIXED: Image Type Restrictions
**Before**: Only checked `image/` content type
**Now**: Accepts all image formats (JPEG, PNG, WebP, etc.)

### ✅ FIXED: Empty Steps Issue
**Before**: Planner sometimes returned no steps
**Now**: Universal fallback creates steps for ANY image type

### ✅ FIXED: Document Type Bias
**Before**: Optimized mainly for prescriptions
**Now**: Works with any document type

## How It Works for Mobile (Expo)

When you scan from Expo:
1. **Camera captures image** → Sends to backend
2. **Vision Engine** analyzes it (works with ANY image)
3. **Planner Engine** creates steps (works with ANY intent)
4. **Executor Engine** performs actions OR returns data

**No restrictions** - it should work with:
- Photos of documents
- Screenshots
- Scanned images
- Any image format

## The Universal Promise

> **"Upload any image, state your intent, and the system will figure out what to do"**

This is achieved through:
1. **Smart Vision** - Understands context, not just text
2. **Adaptive Planning** - Creates steps based on what it sees
3. **Flexible Execution** - Can automate OR just extract data

## Future Enhancements

- Support for PDFs (convert to images first)
- Support for video frames
- Multi-page document handling
- Real-time camera feed analysis

