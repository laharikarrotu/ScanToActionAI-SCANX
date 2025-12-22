"""
Conversational AI endpoint for chat-based interactions
Provides intelligent explanations and answers questions about medical data
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from api.config import settings
from api.dependencies import (
    prescription_extractor, interaction_checker, diet_advisor,
    CACHE_AVAILABLE, cache_manager
)
from core.error_handler import ErrorHandler
from core.logger import get_logger

logger = get_logger("api.routers.chat")
router = APIRouter(prefix="/chat", tags=["chat"])

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None

@router.post("")
async def chat_with_agent(request: Request, chat_request: ChatRequest):
    """
    Conversational AI endpoint - Chat with HealthScan agent
    
    Provides intelligent explanations about:
    - Prescription details
    - Drug interactions
    - Diet recommendations
    - General health questions
    
    **Parameters:**
    - `message`: User's question or message
    - `context`: Current context (prescription_data, interaction_result, diet_data)
    - `conversation_history`: Previous messages in conversation
    
    **Returns:**
    - `response`: AI-generated response
    - `suggestions`: Suggested follow-up questions
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini AI is not available. Please check your GEMINI_API_KEY."
        )
    
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Please set it in your .env file."
        )
    
    try:
        from core.gemini_helper import get_gemini_model_with_fallback
        model = get_gemini_model_with_fallback(api_key=settings.gemini_api_key)
        
        # Build context prompt
        context_str = ""
        if chat_request.context:
            if chat_request.context.get('prescription_data'):
                presc = chat_request.context['prescription_data']
                context_str += f"\n**Current Prescription Data:**\n"
                if presc.get('medications'):
                    for med in presc['medications']:
                        context_str += f"- {med.get('medication_name', 'Unknown')}: {med.get('dosage', '')} {med.get('frequency', '')}\n"
            
            if chat_request.context.get('interaction_result'):
                interactions = chat_request.context['interaction_result']
                warnings = interactions.get('warnings', {})
                context_str += f"\n**Drug Interactions Found:**\n"
                context_str += f"- Major: {len(warnings.get('major', []))}\n"
                context_str += f"- Moderate: {len(warnings.get('moderate', []))}\n"
                context_str += f"- Minor: {len(warnings.get('minor', []))}\n"
            
            if chat_request.context.get('diet_data'):
                diet = chat_request.context['diet_data']
                context_str += f"\n**Diet Information:**\n"
                context_str += f"- Condition: {diet.get('condition', 'Not specified')}\n"
                if diet.get('medications'):
                    context_str += f"- Medications: {diet.get('medications')}\n"
        
        # Build conversation history
        history_str = ""
        if chat_request.conversation_history:
            for msg in chat_request.conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_str += f"{role.capitalize()}: {content}\n"
        
        # Create healthcare-focused prompt
        prompt = f"""You are HealthScan, a specialized AI healthcare assistant focused on medication management and health information. Your primary role is to help users understand their prescriptions, check for drug interactions, and provide diet recommendations.

**Your Core Functions (HealthScan Workflow):**
1. **Prescription Extraction**: Help users understand extracted medication details (name, dosage, frequency, instructions)
2. **Drug Interaction Checking**: Explain drug-drug and drug-allergy interactions clearly
3. **Diet Recommendations**: Provide personalized diet advice based on medical conditions and medications

**Your Capabilities:**
- Explain prescription details in simple, clear, healthcare-focused language
- Answer questions about medications, dosages, side effects, and instructions
- Explain drug interactions and their health implications
- Provide diet recommendations based on medical conditions and medications
- Answer health-related questions with appropriate medical disclaimers

**Critical Guidelines:**
- ALWAYS remind users: "This is not a replacement for professional medical advice. Consult your doctor or pharmacist."
- For serious interactions (major severity), emphasize: "Consult your doctor immediately before taking these medications together."
- Be clear, helpful, and empathetic, but prioritize safety
- Use simple language but maintain medical accuracy
- If you don't know something, say so honestly and recommend consulting a healthcare professional
- Focus on the HealthScan workflow: Prescription → Interactions → Diet

{context_str}

**Conversation History:**
{history_str}

**User's Question:**
{chat_request.message}

**Your Response (be helpful, clear, and remind about consulting professionals):**
"""
        
        # Generate response
        response = model.generate_content(prompt)
        # Handle response - check if it has text attribute
        if hasattr(response, 'text'):
            ai_response = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            ai_response = response.candidates[0].content.parts[0].text
        else:
            ai_response = str(response) if response else "I apologize, but I couldn't generate a response. Please try again."
        
        # Generate suggestions
        suggestions = [
            "Check for drug interactions",
            "Get diet recommendations",
            "Explain medication side effects",
            "What foods to avoid with these medications?",
        ]
        
        return JSONResponse(
            status_code=200,
            content={
                "response": ai_response,
                "suggestions": suggestions,
                "status": "success"
            }
        )
        
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "chat"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        raise HTTPException(
            status_code=500,
            detail=user_friendly_msg
        )

