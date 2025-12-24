"""
Execute verified plan - HITL endpoint
Executes a plan after user verification and editing
"""
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from executor.browser_executor import BrowserExecutor, ExecutionResult
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

async def execute_verified_plan(
    verified_plan: Dict[str, Any],
    verified_data: Dict[str, Any],
    ui_schema: Dict[str, Any],
    start_url: str
) -> ExecutionResult:
    """
    Execute a plan that has been verified and edited by the user (HITL).
    
    Args:
        verified_plan: Action plan with user edits
        verified_data: Extracted data with user edits
        ui_schema: Original UI schema
        start_url: URL to start execution from
    
    Returns:
        ExecutionResult
    """
    try:
        from planner.agent_planner import ActionStep, ActionPlan
        
        # Convert verified plan to ActionPlan
        steps = [ActionStep(**step) for step in verified_plan.get("steps", [])]
        plan = ActionPlan(
            task=verified_plan.get("task", "Execute verified plan"),
            steps=steps,
            estimated_time=verified_plan.get("estimated_time")
        )
        
        # Execute with verified plan
        # Parse allowed domains for SSRF protection
        from api.config import settings
        allowed_domains_list = None
        if settings.allowed_domains:
            allowed_domains_list = [domain.strip() for domain in settings.allowed_domains.split(",") if domain.strip()]
        executor = BrowserExecutor(headless=True, allowed_domains=allowed_domains_list)
        try:
            result = await executor.execute_plan(
                steps=plan.steps,
                ui_schema=ui_schema,
                start_url=start_url
            )
            return result
        finally:
            await executor.close()
            
    except Exception as e:
        logger.error(f"Verified plan execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )

