"""
Planner Engine - Converts user intent + UI schema into actionable steps
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel
import os
import json

class ActionStep(BaseModel):
    step: int
    action: str  # click, fill, select, navigate, wait, read
    target: str  # element ID from UI schema
    value: Optional[str] = None  # for fill/select actions
    description: Optional[str] = None

class ActionPlan(BaseModel):
    task: str
    steps: List[ActionStep]
    estimated_time: Optional[int] = None  # seconds

class PlannerEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
    def create_plan(
        self, 
        user_intent: str, 
        ui_schema: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ActionPlan:
        """
        Takes user intent and UI schema, returns step-by-step action plan
        """
        # Convert UI schema to readable format
        elements_text = "\n".join([
            f"- {elem['id']} ({elem['type']}): {elem.get('label', '')}" + (f" = {elem.get('value', '')}" if elem.get('value') else "")
            for elem in ui_schema.get("elements", [])
        ])
        
        prompt = f"""Given this healthcare-related user intent and UI schema, create a step-by-step action plan.

User Intent: {user_intent}

Available UI Elements:
{elements_text}

Page Type: {ui_schema.get('page_type', 'unknown')}

This is a healthcare context - be careful with sensitive medical information. Focus on helping the user complete medical forms, book appointments, understand prescriptions, or extract insurance information.

Create a JSON plan with this structure:
{{
  "task": "brief_description",
  "steps": [
    {{
      "step": 1,
      "action": "click" | "fill" | "select" | "navigate" | "wait" | "read",
      "target": "element_id_from_schema",
      "value": "value_to_fill_or_select (if needed)",
      "description": "what this step does"
    }}
  ],
  "estimated_time": 5
}}

Rules:
- Use element IDs from the schema
- Order steps logically (fill medical forms before clicking submit)
- For healthcare forms: fill patient info, medical history, insurance details in logical order
- Include waits if needed (e.g., after navigation)
- Be specific with values (dates, text, medical information)
- Only use actions that make sense for the element type
- Don't include destructive actions unless explicitly requested
- For medical data: be accurate and preserve formatting (especially for dates, dosages, medical codes)
- **CRITICAL**: If the intent is to read/extract information, create "read" steps for each relevant element
- **CRITICAL**: If the intent is unclear, create steps to extract all medication/prescription information
- **CRITICAL**: Always return at least 1 step if there are UI elements available
- For prescription/medication documents: create steps to read medication names, dosages, instructions
- For forms: create steps to fill or read form fields based on intent

Return ONLY valid JSON, no other text."""

        if context:
            prompt += f"\n\nAdditional context: {json.dumps(context)}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a task planning agent. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result_text = response.choices[0].message.content
            result_dict = json.loads(result_text)
            
            # Convert to ActionPlan
            steps = []
            try:
                steps = [ActionStep(**step) for step in result_dict.get("steps", [])]
            except Exception as step_error:
                import logging
                logging.warning(f"Error parsing steps from LLM response: {step_error}")
                # Continue to fallback logic
            
            # ALWAYS create fallback steps if we have elements (even if LLM returned steps)
            # This ensures we always have steps for any image type
            if ui_schema.get("elements") and not steps:
                elements = ui_schema.get("elements", [])
                intent_lower = user_intent.lower() if user_intent else ""
                
                # Determine action type based on intent
                if any(word in intent_lower for word in ["fill", "enter", "input", "submit", "complete", "form"]):
                    action_type = "fill"
                elif any(word in intent_lower for word in ["click", "select", "choose", "press", "button"]):
                    action_type = "click"
                elif any(word in intent_lower for word in ["navigate", "go", "visit", "open", "browse"]):
                    action_type = "navigate"
                else:
                    # Default: read/extract for any other intent
                    action_type = "read"
                
                # Create steps based on element types and intent
                step_num = 1
                for i, elem in enumerate(elements[:15]):  # Process up to 15 elements
                    elem_type = elem.get("type", "text").lower()
                    
                    # Determine appropriate action for this element
                    if action_type == "fill" and elem_type in ["input", "text", "select", "textarea"]:
                        steps.append(ActionStep(
                            step=step_num,
                            action="fill",
                            target=elem.get("id", f"elem_{i}"),
                            value=elem.get("value") or "",
                            description=f"Fill {elem.get('label', 'field')[:50]}"
                        ))
                        step_num += 1
                    elif action_type == "click" and elem_type in ["button", "link", "checkbox", "radio"]:
                        steps.append(ActionStep(
                            step=step_num,
                            action="click",
                            target=elem.get("id", f"elem_{i}"),
                            description=f"Click {elem.get('label', 'element')[:50]}"
                        ))
                        step_num += 1
                    else:
                        # For read/navigate/default, create read steps for all elements
                        steps.append(ActionStep(
                            step=step_num,
                            action="read",
                            target=elem.get("id", f"elem_{i}"),
                            description=f"Read {elem.get('type', 'text')}: {elem.get('label', '')[:50]}"
                        ))
                        step_num += 1
                
                # If still no steps (shouldn't happen), create at least one read step
                if not steps and elements:
                    steps.append(ActionStep(
                        step=1,
                        action="read",
                        target=elements[0].get("id", "elem_0"),
                        description=f"Process document: {ui_schema.get('page_type', 'document')}"
                    ))
            
            # FINAL CHECK: Ensure we always have steps if elements exist
            if not steps and ui_schema.get("elements"):
                # Last resort: create simple read steps for all elements
                elements = ui_schema.get("elements", [])
                for i, elem in enumerate(elements[:10]):
                    steps.append(ActionStep(
                        step=i + 1,
                        action="read",
                        target=elem.get("id", f"elem_{i}"),
                        description=f"Read: {elem.get('label', '')[:50]}"
                    ))
            
            return ActionPlan(
                task=result_dict.get("task", "Process document") if steps else "Extract information",
                steps=steps,
                estimated_time=result_dict.get("estimated_time", len(steps) * 2)
            )
            
        except Exception as e:
            # Log error but still create steps from elements
            import logging
            logging.error(f"Planner error: {str(e)}", exc_info=True)
            
            # Even on error, create steps from available elements
            steps = []
            if ui_schema.get("elements"):
                elements = ui_schema.get("elements", [])
                intent_lower = user_intent.lower() if user_intent else ""
                
                # Determine action type
                if any(word in intent_lower for word in ["fill", "enter", "input", "submit", "complete", "form"]):
                    action_type = "fill"
                elif any(word in intent_lower for word in ["click", "select", "choose", "press", "button"]):
                    action_type = "click"
                else:
                    action_type = "read"
                
                # Create steps for all elements
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
            
            # If still no steps, create at least one
            if not steps and ui_schema.get("elements"):
                steps.append(ActionStep(
                    step=1,
                    action="read",
                    target=ui_schema["elements"][0].get("id", "elem_0"),
                    description=f"Process {ui_schema.get('page_type', 'document')}"
                ))
            
            return ActionPlan(
                task=f"Process {ui_schema.get('page_type', 'document')} (fallback)",
                steps=steps,
                estimated_time=len(steps) * 2
            )

