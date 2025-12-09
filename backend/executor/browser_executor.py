"""
Browser Executor - Uses Playwright to execute action plans
"""
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from pydantic import BaseModel
import asyncio
import os

class ActionStep(BaseModel):
    step: int
    action: str
    target: str
    value: Optional[str] = None
    description: Optional[str] = None

class ExecutionResult(BaseModel):
    status: str  # success, error, partial
    message: str
    final_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    logs: List[str] = []

class BrowserExecutor:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def initialize(self):
        """Initialize browser session"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def close(self):
        """Close browser session"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    def _find_element_selector(self, element_id: str, ui_schema: Dict[str, Any]) -> Optional[str]:
        """
        Maps element ID from schema to Playwright selector
        This is the tricky part - heuristic matching
        """
        # Find element in schema
        element = None
        for elem in ui_schema.get("elements", []):
            if elem.get("id") == element_id:
                element = elem
                break
        
        if not element:
            return None
        
        elem_type = element.get("type", "")
        label = element.get("label", "")
        value = element.get("value", "")
        
        # Heuristic selectors based on type and label
        if elem_type == "button":
            # Try multiple strategies
            if label:
                # Text-based selector
                return f'button:has-text("{label}")'
            return "button"
        
        elif elem_type == "input":
            if label:
                # Try to find input near label
                return f'input[placeholder*="{label}"]'
            return "input"
        
        elif elem_type == "link":
            if label:
                return f'a:has-text("{label}")'
            return "a"
        
        # Fallback
        return None
    
    async def execute_plan(
        self,
        steps: List[ActionStep],
        ui_schema: Dict[str, Any],
        start_url: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a list of action steps
        """
        if not self.page:
            await self.initialize()
        
        result = ExecutionResult(
            status="in_progress",
            message="Starting execution",
            logs=[]
        )
        
        try:
            # Navigate to start URL if provided
            if start_url:
                result.logs.append(f"Navigating to {start_url}")
                await self.page.goto(start_url, wait_until="networkidle")
            
            # Execute each step
            for step in steps:
                result.logs.append(f"Step {step.step}: {step.action} on {step.target}")
                
                selector = self._find_element_selector(step.target, ui_schema)
                
                if not selector:
                    result.logs.append(f"Warning: Could not find selector for {step.target}")
                    continue
                
                try:
                    if step.action == "click":
                        await self.page.click(selector, timeout=5000)
                        await asyncio.sleep(0.5)  # Small delay
                    
                    elif step.action == "fill":
                        await self.page.fill(selector, step.value or "", timeout=5000)
                    
                    elif step.action == "select":
                        await self.page.select_option(selector, step.value or "", timeout=5000)
                    
                    elif step.action == "navigate":
                        await self.page.goto(step.value or "", wait_until="networkidle")
                    
                    elif step.action == "wait":
                        await asyncio.sleep(int(step.value or 1))
                    
                    elif step.action == "read":
                        text = await self.page.text_content(selector)
                        result.logs.append(f"Read: {text}")
                    
                except Exception as e:
                    result.logs.append(f"Error in step {step.step}: {str(e)}")
                    # Continue with next step
            
            # Get final state
            result.final_url = self.page.url
            
            # Take screenshot
            screenshot_dir = "memory/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = f"{screenshot_dir}/result_{int(asyncio.get_event_loop().time())}.png"
            await self.page.screenshot(path=screenshot_path)
            result.screenshot_path = screenshot_path
            
            result.status = "success"
            result.message = "Execution completed"
            
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            result.message = f"Execution failed: {str(e)}"
        
        return result

