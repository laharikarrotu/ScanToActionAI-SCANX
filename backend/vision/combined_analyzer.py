"""
Combined Analyzer - Vision + Planning in ONE API call
Uses Gemini Pro 1.5 multimodal to do both tasks simultaneously
Reduces 2 API calls → 1 call (50% cost/time savings)
"""
import base64
from typing import Optional, Dict, Any, Tuple
import os
import json
import re
from vision.ui_detector import UIElement, UISchema
from planner.agent_planner import ActionStep, ActionPlan
from vision.ocr_preprocessor import OCRPreprocessor

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class CombinedAnalyzer:
    """
    Combined analyzer that does vision analysis AND planning in ONE Gemini API call
    This reduces 2 separate API calls to 1, saving 50% cost and time
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required")
        
        genai.configure(api_key=self.api_key)
        from core.gemini_helper import get_gemini_model_with_fallback
        self.model = get_gemini_model_with_fallback(api_key=self.api_key)
        self.ocr_preprocessor = OCRPreprocessor()
    
    def analyze_and_plan(
        self,
        image_data: bytes,
        user_intent: str,
        context: Optional[Dict[str, Any]] = None,
        hint: Optional[str] = None
    ) -> Tuple[UISchema, ActionPlan]:
        """
        Analyze image AND create action plan in ONE API call
        
        Returns:
            Tuple[UISchema, ActionPlan]: Vision schema and action plan
        """
        # Preprocess image
        try:
            processed_image = self.ocr_preprocessor.preprocess_image(image_data)
        except (ValueError, IOError, OSError, AttributeError):
            # Fallback to original if preprocessing fails
            processed_image = image_data
        
        # Extract OCR text
        ocr_result = self.ocr_preprocessor.extract_text(processed_image, preprocess=False)
        ocr_text = ocr_result.get("text", "")
        
        # Build combined prompt that does both vision and planning
        prompt = self._build_combined_prompt(user_intent, ocr_text, context, hint)
        
        try:
            # Convert image to format Gemini expects
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(processed_image))
            
            # Single API call for BOTH vision and planning
            response = self.model.generate_content(
                [prompt, image],
                generation_config={
                    "temperature": 0.1,  # Lower temperature for more consistent results
                    "max_output_tokens": 6000,  # More tokens for combined response
                    # response_mime_type removed - not supported in all API versions
                }
            )
            
            result_text = response.text
            
            # Parse JSON response
            try:
                result_dict = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                if json_match:
                    result_dict = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse JSON from Gemini response")
            
            # Extract UI Schema
            ui_schema = self._parse_ui_schema(result_dict, ocr_text)
            
            # Extract Action Plan
            action_plan = self._parse_action_plan(result_dict, ui_schema, user_intent)
            
            return ui_schema, action_plan
            
        except Exception as e:
            import logging
            logging.error(f"Combined analyzer error: {str(e)}", exc_info=True)
            
            # Fallback: Create minimal schema and plan
            elements = []
            if ocr_text:
                ocr_lines = [line.strip() for line in ocr_text.split('\n') if line.strip()][:10]
                for i, line in enumerate(ocr_lines):
                    elements.append(UIElement(
                        id=f"ocr_text_{i}",
                        type="text",
                        label=line
                    ))
            
            if not elements:
                elements = [UIElement(id="elem_0", type="text", label="Document detected")]
            
            ui_schema = UISchema(
                page_type="other",
                url_hint=None,
                elements=elements
            )
            
            # Create fallback plan
            steps = []
            for i, elem in enumerate(elements[:5]):
                steps.append(ActionStep(
                    step=i + 1,
                    action="read",
                    target=elem.id,
                    description=f"Read: {elem.label[:50]}"
                ))
            
            action_plan = ActionPlan(
                task="Process document (fallback)",
                steps=steps,
                estimated_time=len(steps) * 2
            )
            
            return ui_schema, action_plan
    
    def _build_combined_prompt(
        self,
        user_intent: str,
        ocr_text: str,
        context: Optional[Dict[str, Any]],
        hint: Optional[str]
    ) -> str:
        """Build a prompt that does both vision analysis AND planning"""
        prompt = f"""You are an AI assistant specialized in healthcare document processing. Analyze this image and create an action plan in ONE response.

TASK 1: VISION ANALYSIS
Extract all UI elements, text, and structured data from the image.

TASK 2: ACTION PLANNING
Based on the user's intent, create a step-by-step action plan.

USER INTENT: {user_intent}

OCR EXTRACTED TEXT (use this to help):
{ocr_text[:2000] if ocr_text else "No OCR text available"}

{f"CONTEXT: {json.dumps(context)}" if context else ""}
{f"HINT: {hint}" if hint else ""}

Return a JSON object with this EXACT structure:
{{
  "ui_schema": {{
    "page_type": "prescription" | "medical_form" | "insurance_card" | "appointment_page" | "lab_result" | "other",
    "url_hint": "URL if visible, or null",
    "elements": [
      {{
        "id": "unique_id_1",
        "type": "text" | "medication" | "dosage" | "prescriber" | "pharmacy" | "input" | "button" | "label" | "data",
        "label": "visible text or label (REQUIRED)",
        "value": "current value if input/data field, or null",
        "position": {{"x": 100, "y": 200}} or null
      }}
    ]
  }},
  "action_plan": {{
    "task": "brief_description_of_what_we_are_doing",
    "steps": [
      {{
        "step": 1,
        "action": "read" | "fill" | "click" | "select" | "navigate" | "wait",
        "target": "element_id_from_ui_schema",
        "value": "value_to_fill_if_action_is_fill",
        "description": "Step 1: [action] [target]"
      }}
    ],
    "estimated_time": 5
  }}
}}

CRITICAL RULES:
1. The "elements" array MUST NOT be empty - extract at least 3-10 elements
2. Extract EVERY piece of visible text as a separate element
3. The "steps" array MUST have at least 2-5 steps if elements are available
4. Use element IDs from ui_schema in the action plan
5. For "fill" actions, infer reasonable values based on user intent
6. For "read" actions, specify which elements to extract data from

ANALYZE THE INTENT:
- If user wants to "fill" or "complete" → Create "fill" actions for input fields
- If user wants to "read" or "extract" → Create "read" actions to extract data
- If user wants to "click" or "submit" → Create "click" actions for buttons
- If user wants to "book" or "schedule" → Create fill + click actions for forms

Return ONLY valid JSON, no other text or markdown."""
        return prompt
    
    def _parse_ui_schema(self, result_dict: Dict[str, Any], ocr_text: str) -> UISchema:
        """Parse UI schema from combined response"""
        ui_schema_data = result_dict.get("ui_schema", {})
        
        elements = []
        for elem in ui_schema_data.get("elements", []):
            try:
                if not elem.get("id"):
                    elem["id"] = f"elem_{len(elements)}"
                if not elem.get("type"):
                    elem["type"] = "text"
                if not elem.get("label"):
                    elem["label"] = elem.get("value", "") or "Unknown"
                elements.append(UIElement(**elem))
            except Exception:
                elements.append(UIElement(
                    id=f"elem_{len(elements)}",
                    type="text",
                    label=str(elem.get("label", elem.get("value", "Unknown")))
                ))
        
        # Fallback: Create elements from OCR if none found
        if not elements and ocr_text:
            ocr_lines = [line.strip() for line in ocr_text.split('\n') if line.strip()][:10]
            for i, line in enumerate(ocr_lines):
                elements.append(UIElement(
                    id=f"ocr_text_{i}",
                    type="text",
                    label=line
                ))
        
        if not elements:
            elements = [UIElement(id="elem_0", type="text", label="Document detected")]
        
        return UISchema(
            page_type=ui_schema_data.get("page_type", "other"),
            url_hint=ui_schema_data.get("url_hint"),
            elements=elements
        )
    
    def _parse_action_plan(
        self,
        result_dict: Dict[str, Any],
        ui_schema: UISchema,
        user_intent: str
    ) -> ActionPlan:
        """Parse action plan from combined response"""
        action_plan_data = result_dict.get("action_plan", {})
        
        steps = []
        try:
            steps = [ActionStep(**step) for step in action_plan_data.get("steps", [])]
        except Exception:
            pass
        
        # Fallback: Create steps from elements if plan is empty
        if not steps and ui_schema.elements:
            elements = ui_schema.elements
            intent_lower = user_intent.lower() if user_intent else ""
            
            action_type = "read"
            if any(word in intent_lower for word in ["fill", "enter", "input", "submit", "complete", "form"]):
                action_type = "fill"
            elif any(word in intent_lower for word in ["click", "select", "choose", "press", "button"]):
                action_type = "click"
            
            for i, elem in enumerate(elements[:15]):
                if action_type == "fill" and elem.type.lower() in ["input", "text", "select", "textarea"]:
                    steps.append(ActionStep(
                        step=i + 1,
                        action="fill",
                        target=elem.id,
                        value=elem.value or "",
                        description=f"Fill {elem.label[:50]}"
                    ))
                elif action_type == "click" and elem.type.lower() in ["button", "link", "checkbox", "radio"]:
                    steps.append(ActionStep(
                        step=i + 1,
                        action="click",
                        target=elem.id,
                        description=f"Click {elem.label[:50]}"
                    ))
                else:
                    steps.append(ActionStep(
                        step=i + 1,
                        action="read",
                        target=elem.id,
                        description=f"Read {elem.type}: {elem.label[:50]}"
                    ))
        
        # Final safety check
        if not steps and ui_schema.elements:
            for i, elem in enumerate(ui_schema.elements[:10]):
                steps.append(ActionStep(
                    step=i + 1,
                    action="read",
                    target=elem.id,
                    description=f"Read: {elem.label[:50]}"
                ))
        
        return ActionPlan(
            task=action_plan_data.get("task", "Process document"),
            steps=steps,
            estimated_time=action_plan_data.get("estimated_time", len(steps) * 2)
        )
