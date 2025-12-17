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
            f"- {elem['id']} ({elem['type']}): {elem.get('label', '')} {f'= {elem.get(\"value\", \"\")}' if elem.get('value') else ''}"
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
            steps = [ActionStep(**step) for step in result_dict.get("steps", [])]
            
            return ActionPlan(
                task=result_dict.get("task", "unknown"),
                steps=steps,
                estimated_time=result_dict.get("estimated_time")
            )
            
        except Exception as e:
            # Return minimal plan on error
            return ActionPlan(
                task="error",
                steps=[],
                estimated_time=0
            )

