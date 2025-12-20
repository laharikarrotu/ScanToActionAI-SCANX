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
        # Confidence thresholds for element reliability
        self.HIGH_CONFIDENCE_THRESHOLD = 0.7
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.4
        self.LOW_CONFIDENCE_THRESHOLD = 0.0
    
    def _calculate_element_confidence(self, element: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a UI element.
        
        Factors:
        - Element has explicit confidence score: use it
        - Element type specificity (button > text)
        - Element has value (filled fields are more reliable)
        - Element has position (positioned elements are more reliable)
        
        Returns:
            Confidence score 0.0 to 1.0
        """
        # If element has explicit confidence, use it
        if element.get("confidence") is not None:
            return float(element.get("confidence", 0.5))
        
        # Base confidence on element type specificity
        elem_type = element.get("type", "text").lower()
        type_confidence = {
            "button": 0.8,
            "input": 0.7,
            "select": 0.7,
            "link": 0.6,
            "checkbox": 0.6,
            "radio": 0.6,
            "medication": 0.9,  # Medical-specific types are high confidence
            "dosage": 0.9,
            "prescriber": 0.8,
            "pharmacy": 0.8,
            "text": 0.5,  # Generic text is lower confidence
            "label": 0.6,
            "data": 0.5
        }.get(elem_type, 0.5)
        
        # Boost confidence if element has value (filled fields are more reliable)
        if element.get("value"):
            type_confidence += 0.1
        
        # Boost confidence if element has position (positioned elements are more reliable)
        if element.get("position"):
            type_confidence += 0.1
        
        # Boost confidence if element has a clear label
        if element.get("label") and len(element.get("label", "")) > 3:
            type_confidence += 0.05
        
        return min(1.0, type_confidence)
    
    def _categorize_elements_by_confidence(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize elements by confidence level.
        
        Returns:
            {
                "high": [...],      # confidence >= 0.7
                "medium": [...],    # 0.4 <= confidence < 0.7
                "low": [...]        # confidence < 0.4
            }
        """
        categorized = {"high": [], "medium": [], "low": []}
        
        for elem in elements:
            confidence = self._calculate_element_confidence(elem)
            # Add confidence to element for later use
            elem["_calculated_confidence"] = confidence
            
            if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                categorized["high"].append(elem)
            elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                categorized["medium"].append(elem)
            else:
                categorized["low"].append(elem)
        
        return categorized
    
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
            
            # ENHANCED FALLBACK: Use confidence-based routing for smarter fallbacks
            if ui_schema.get("elements") and not steps:
                elements = ui_schema.get("elements", [])
                
                # Categorize elements by confidence
                categorized = self._categorize_elements_by_confidence(elements)
                
                intent_lower = user_intent.lower() if user_intent else ""
                
                # Determine action type based on intent
                if any(word in intent_lower for word in ["fill", "enter", "input", "submit", "complete", "form"]):
                    action_type = "fill"
                elif any(word in intent_lower for word in ["click", "select", "choose", "press", "button"]):
                    action_type = "click"
                elif any(word in intent_lower for word in ["navigate", "go", "visit", "open", "browse"]):
                    action_type = "navigate"
                else:
                    action_type = "read"
                
                step_num = 1
                
                # STRATEGY 1: Process high-confidence elements first (direct actions)
                for elem in categorized["high"][:10]:  # Limit to top 10 high-confidence
                    elem_type = elem.get("type", "text").lower()
                    confidence = elem.get("_calculated_confidence", 0.7)
                    
                    if action_type == "fill" and elem_type in ["input", "text", "select", "textarea"]:
                        steps.append(ActionStep(
                            step=step_num,
                            action="fill",
                            target=elem.get("id", f"elem_{step_num}"),
                            value=elem.get("value") or "",
                            description=f"Fill {elem.get('label', 'field')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                    elif action_type == "click" and elem_type in ["button", "link", "checkbox", "radio"]:
                        steps.append(ActionStep(
                            step=step_num,
                            action="click",
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Click {elem.get('label', 'element')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                    else:
                        steps.append(ActionStep(
                            step=step_num,
                            action="read",
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Read {elem.get('type', 'text')}: {elem.get('label', '')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                
                # STRATEGY 2: Process medium-confidence elements (with validation)
                for elem in categorized["medium"][:5]:  # Limit to top 5 medium-confidence
                    elem_type = elem.get("type", "text").lower()
                    confidence = elem.get("_calculated_confidence", 0.5)
                    
                    # For medium confidence, prefer read actions (safer)
                    if action_type == "read" or confidence < 0.6:
                        steps.append(ActionStep(
                            step=step_num,
                            action="read",
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Read {elem.get('label', '')[:50]} (verify - confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                    elif action_type == "fill" and elem_type in ["input", "text", "select"]:
                        # Only fill if high confidence
                        steps.append(ActionStep(
                            step=step_num,
                            action="read",  # Read first to verify
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Verify before filling: {elem.get('label', '')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                
                # STRATEGY 3: Low-confidence elements - OCR fallback or skip
                # Only include if we have very few steps
                if len(steps) < 3 and categorized["low"]:
                    for elem in categorized["low"][:3]:  # Only top 3 low-confidence
                        steps.append(ActionStep(
                            step=step_num,
                            action="read",
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Attempt to read (low confidence): {elem.get('label', '')[:30]}"
                        ))
                        step_num += 1
                
                # If still no steps, create at least one read step from highest confidence element
                if not steps and elements:
                    # Sort all elements by confidence
                    sorted_elements = sorted(elements, key=lambda e: self._calculate_element_confidence(e), reverse=True)
                    best_elem = sorted_elements[0]
                    steps.append(ActionStep(
                        step=1,
                        action="read",
                        target=best_elem.get("id", "elem_0"),
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
            # Log error but still create steps from elements using confidence-based fallback
            import logging
            logging.error(f"Planner error: {str(e)}", exc_info=True)
            
            # Even on error, create steps from available elements using confidence-based routing
            steps = []
            if ui_schema.get("elements"):
                elements = ui_schema.get("elements", [])
                
                # Use confidence-based categorization
                categorized = self._categorize_elements_by_confidence(elements)
                
                intent_lower = user_intent.lower() if user_intent else ""
                
                # Determine action type
                if any(word in intent_lower for word in ["fill", "enter", "input", "submit", "complete", "form"]):
                    action_type = "fill"
                elif any(word in intent_lower for word in ["click", "select", "choose", "press", "button"]):
                    action_type = "click"
                else:
                    action_type = "read"
                
                step_num = 1
                
                # Prioritize high-confidence elements even in error fallback
                for elem in categorized["high"][:10]:
                    elem_type = elem.get("type", "text").lower()
                    confidence = elem.get("_calculated_confidence", 0.7)
                    
                    if action_type == "fill" and elem_type in ["input", "text", "select", "textarea"]:
                        steps.append(ActionStep(
                            step=step_num,
                            action="fill",
                            target=elem.get("id", f"elem_{step_num}"),
                            value=elem.get("value") or "",
                            description=f"Fill {elem.get('label', 'field')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                    elif action_type == "click" and elem_type in ["button", "link", "checkbox", "radio"]:
                        steps.append(ActionStep(
                            step=step_num,
                            action="click",
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Click {elem.get('label', 'element')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                    else:
                        steps.append(ActionStep(
                            step=step_num,
                            action="read",
                            target=elem.get("id", f"elem_{step_num}"),
                            description=f"Read {elem.get('type', 'text')}: {elem.get('label', '')[:50]} (confidence: {confidence:.2f})"
                        ))
                        step_num += 1
                
                # Add medium-confidence elements as read-only
                for elem in categorized["medium"][:5]:
                    steps.append(ActionStep(
                        step=step_num,
                        action="read",
                        target=elem.get("id", f"elem_{step_num}"),
                        description=f"Read {elem.get('label', '')[:50]} (verify)"
                    ))
                    step_num += 1
            
            # If still no steps, create at least one from highest confidence element
            if not steps and ui_schema.get("elements"):
                sorted_elements = sorted(ui_schema["elements"], 
                                       key=lambda e: self._calculate_element_confidence(e), 
                                       reverse=True)
                best_elem = sorted_elements[0]
                steps.append(ActionStep(
                    step=1,
                    action="read",
                    target=best_elem.get("id", "elem_0"),
                    description=f"Process {ui_schema.get('page_type', 'document')} (fallback)"
                ))
            
            return ActionPlan(
                task=f"Process {ui_schema.get('page_type', 'document')} (fallback)",
                steps=steps,
                estimated_time=len(steps) * 2
            )

