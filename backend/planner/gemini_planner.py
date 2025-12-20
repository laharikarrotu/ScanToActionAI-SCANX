"""
Gemini Planner Engine - Alternative to OpenAI for task planning
Uses Google Gemini Pro 1.5 for reasoning
"""
from typing import List, Dict, Any, Optional
import os
import json
from planner.agent_planner import ActionStep, ActionPlan

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class GeminiPlannerEngine:
    """Planner engine using Google Gemini Pro 1.5"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def create_plan(
        self,
        user_intent: str,
        ui_schema: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ActionPlan:
        """Create action plan using Gemini"""
        # Convert UI schema to readable format
        elements_text = "\n".join([
            f"- {elem['id']} ({elem['type']}): {elem.get('label', '')}" + (f" = {elem.get('value', '')}" if elem.get('value') else "")
            for elem in ui_schema.get("elements", [])
        ])
        
        prompt = f"""You are an AI assistant that creates actionable step-by-step plans for healthcare document processing.

User Intent: {user_intent}

Available UI Elements:
{elements_text}

Page Type: {ui_schema.get('page_type', 'unknown')}

YOUR TASK: Create a detailed action plan that accomplishes the user's intent.

ANALYZE THE INTENT:
- If user wants to "fill" or "complete" → Create "fill" actions for input fields
- If user wants to "read" or "extract" → Create "read" actions to extract data
- If user wants to "click" or "submit" → Create "click" actions for buttons
- If user wants to "book" or "schedule" → Create fill + click actions for forms

MANDATORY REQUIREMENTS:
1. You MUST create at least 2-5 steps if elements are available
2. Each step must have: step number, action type, target element ID, and description
3. Use the exact element IDs from the UI schema above
4. For "fill" actions, infer reasonable values based on the user intent
5. For "read" actions, specify which elements to extract data from

Return ONLY this JSON structure (no markdown, no explanations):
{{
  "task": "brief_description_of_what_we_are_doing",
  "steps": [
    {{
      "step": 1,
      "action": "fill",
      "target": "element_id_from_above",
      "value": "value_to_fill_based_on_intent",
      "description": "Step 1: Fill [field name] with [value]"
    }},
    {{
      "step": 2,
      "action": "click",
      "target": "element_id_from_above",
      "description": "Step 2: Click [button/link name]"
    }}
  ],
  "estimated_time": 5
}}

CRITICAL: Return at least 2-5 steps. Use element IDs exactly as shown above."""

        if context:
            prompt += f"\n\nAdditional context: {json.dumps(context)}"
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 2000,
                }
            )
            
            result_text = response.text.strip()
            
            # Try to extract JSON if wrapped in markdown
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            elif result_text.startswith('{') and result_text.endswith('}'):
                # Already JSON
                pass
            else:
                # Try to find JSON object in the text
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            result_dict = json.loads(result_text)
            
            # Convert to ActionPlan
            steps = []
            try:
                steps = [ActionStep(**step) for step in result_dict.get("steps", [])]
            except Exception:
                pass
            
            # Fallback: Create steps from elements
            if not steps and ui_schema.get("elements"):
                elements = ui_schema.get("elements", [])
                intent_lower = user_intent.lower() if user_intent else ""
                
                action_type = "read"
                if any(word in intent_lower for word in ["fill", "enter", "input", "submit", "complete", "form"]):
                    action_type = "fill"
                elif any(word in intent_lower for word in ["click", "select", "choose", "press", "button"]):
                    action_type = "click"
                
                for i, elem in enumerate(elements[:15]):
                    if action_type == "fill" and elem.get("type", "").lower() in ["input", "text", "select", "textarea"]:
                        steps.append(ActionStep(
                            step=i + 1,
                            action="fill",
                            target=elem.get("id", f"elem_{i}"),
                            value=elem.get("value") or "",
                            description=f"Fill {elem.get('label', 'field')[:50]}"
                        ))
                    elif action_type == "click" and elem.get("type", "").lower() in ["button", "link", "checkbox", "radio"]:
                        steps.append(ActionStep(
                            step=i + 1,
                            action="click",
                            target=elem.get("id", f"elem_{i}"),
                            description=f"Click {elem.get('label', 'element')[:50]}"
                        ))
                    else:
                        steps.append(ActionStep(
                            step=i + 1,
                            action="read",
                            target=elem.get("id", f"elem_{i}"),
                            description=f"Read {elem.get('type', 'text')}: {elem.get('label', '')[:50]}"
                        ))
            
            # Final safety check
            if not steps and ui_schema.get("elements"):
                elements = ui_schema.get("elements", [])
                for i, elem in enumerate(elements[:10]):
                    steps.append(ActionStep(
                        step=i + 1,
                        action="read",
                        target=elem.get("id", f"elem_{i}"),
                        description=f"Read: {elem.get('label', '')[:50]}"
                    ))
            
            return ActionPlan(
                task=result_dict.get("task", "Process document"),
                steps=steps,
                estimated_time=result_dict.get("estimated_time", len(steps) * 2)
            )
            
        except Exception as e:
            import logging
            logging.error(f"Gemini planner error: {str(e)}", exc_info=True)
            
            # Create fallback steps
            steps = []
            if ui_schema.get("elements"):
                elements = ui_schema.get("elements", [])
                for i, elem in enumerate(elements[:10]):
                    steps.append(ActionStep(
                        step=i + 1,
                        action="read",
                        target=elem.get("id", f"elem_{i}"),
                        description=f"Read: {elem.get('label', '')[:50]}"
                    ))
            
            return ActionPlan(
                task=f"Process {ui_schema.get('page_type', 'document')} (fallback)",
                steps=steps,
                estimated_time=len(steps) * 2
            )

