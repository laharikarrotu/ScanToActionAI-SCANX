# OpenAI Credits Guide

## Do You Need to Buy OpenAI Credits?

### Short Answer:
**YES** - You need OpenAI credits to use GPT-4o Vision and Planning.

### Current Status:
- ❌ **Quota Exceeded** (429 error)
- ✅ **Fallback works** (creates steps without OpenAI, but less intelligent)

## Options:

### Option 1: Add Credits (Recommended)
**Cost**: $5-10 for testing, $20-50 for development

**Steps:**
1. Go to https://platform.openai.com/account/billing
2. Add payment method
3. Add $5-10 credits
4. System will work immediately

**Cost per Request:**
- Vision API: ~$0.01-0.05 per image
- Planner API: ~$0.01-0.03 per request
- **Total**: ~$0.02-0.08 per image upload

**Monthly Estimate:**
- 100 images: ~$2-8/month
- 500 images: ~$10-40/month

### Option 2: Use Free Tier (Limited)
- Some accounts get $5 free credits
- Check: https://platform.openai.com/usage
- Limited to basic models

### Option 3: Use Fallback Only (Free but Limited)
**Current Status**: ✅ Fallback is working!

**What Works:**
- ✅ Creates steps from detected elements
- ✅ Works for any image type
- ✅ No API costs

**Limitations:**
- ❌ Less intelligent planning
- ❌ No LLM reasoning
- ❌ Basic step generation only

## Recommendation:

**For Development/Testing:**
- Add $5-10 credits (one-time)
- Test thoroughly
- Monitor usage at platform.openai.com/usage

**For Production:**
- Start with $20-50 credits
- Monitor costs
- Implement caching to reduce API calls

## Current System Status:

✅ **Fallback is working** - You can test without credits!
⚠️ **Better results** - Need OpenAI credits for intelligent planning

Try uploading an image now - the fallback will create steps even without OpenAI credits!

