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
        self.playwright = None  # Store playwright instance
    
    async def initialize(self):
        """Initialize browser session"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def close(self):
        """Close browser session"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            # Log but don't raise - cleanup should be best effort
            import logging
            logging.warning(f"Error closing browser executor: {e}")
    
    async def _find_element_selector(self, element_id: str, ui_schema: Dict[str, Any], page: Page) -> Optional[str]:
        """
        Improved element selector matching with multiple fallback strategies
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
        position = element.get("position", {})
        
        # Strategy 1: Try exact text match
        if label:
            selectors_to_try = []
            
            if elem_type == "button":
                selectors_to_try = [
                    f'button:has-text("{label}")',
                    f'button[aria-label*="{label}"]',
                    f'input[type="button"][value*="{label}"]',
                    f'input[type="submit"][value*="{label}"]',
                    f'[role="button"]:has-text("{label}")',
                ]
            elif elem_type == "input":
                selectors_to_try = [
                    f'input[placeholder*="{label}"]',
                    f'input[name*="{label.lower().replace(" ", "_")}"]',
                    f'input[id*="{label.lower().replace(" ", "_")}"]',
                    f'label:has-text("{label}") + input',
                    f'label:has-text("{label}") ~ input',
                ]
            elif elem_type == "link":
                selectors_to_try = [
                    f'a:has-text("{label}")',
                    f'a[href*="{label.lower()}"]',
                ]
            elif elem_type == "select":
                selectors_to_try = [
                    f'select[name*="{label.lower().replace(" ", "_")}"]',
                    f'label:has-text("{label}") + select',
                ]
            
            # Try each selector
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        return selector
                except:
                    continue
        
        # Strategy 2: Try by type only (fallback)
        type_selectors = {
            "button": "button",
            "input": "input",
            "link": "a",
            "select": "select",
        }
        
        if elem_type in type_selectors:
            return type_selectors[elem_type]
        
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
            successful_steps = 0
            for step in steps:
                result.logs.append(f"Step {step.step}: {step.action} on {step.target}")
                
                selector = await self._find_element_selector(step.target, ui_schema, self.page)
                
                if not selector:
                    result.logs.append(f"⚠️ Warning: Could not find selector for {step.target}")
                    # Try to find by partial match
                    element = next((e for e in ui_schema.get("elements", []) if e.get("id") == step.target), None)
                    if element and element.get("label"):
                        # Last resort: try fuzzy text search
                        try:
                            text_selector = f'text="{element.get("label")}"'
                            await self.page.wait_for_selector(text_selector, timeout=2000, state="visible")
                            selector = text_selector
                            result.logs.append(f"✓ Found element using text search")
                        except:
                            result.logs.append(f"✗ Skipping step {step.step} - element not found")
                            continue
                    else:
                        continue
                
                try:
                    # Wait for element to be visible
                    await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    
                    if step.action == "click":
                        await self.page.click(selector, timeout=5000)
                        await asyncio.sleep(0.5)
                        result.logs.append(f"✓ Clicked {step.target}")
                        successful_steps += 1
                    
                    elif step.action == "fill":
                        await self.page.fill(selector, step.value or "", timeout=5000)
                        await asyncio.sleep(0.3)
                        result.logs.append(f"✓ Filled {step.target} with '{step.value}'")
                        successful_steps += 1
                    
                    elif step.action == "select":
                        await self.page.select_option(selector, step.value or "", timeout=5000)
                        result.logs.append(f"✓ Selected '{step.value}' in {step.target}")
                        successful_steps += 1
                    
                    elif step.action == "navigate":
                        await self.page.goto(step.value or "", wait_until="networkidle", timeout=30000)
                        result.logs.append(f"✓ Navigated to {step.value}")
                        successful_steps += 1
                    
                    elif step.action == "wait":
                        wait_time = int(step.value or 1)
                        await asyncio.sleep(wait_time)
                        result.logs.append(f"✓ Waited {wait_time}s")
                        successful_steps += 1
                    
                    elif step.action == "read":
                        text = await self.page.text_content(selector)
                        result.logs.append(f"✓ Read: {text[:50]}...")
                        successful_steps += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    result.logs.append(f"✗ Error in step {step.step}: {error_msg}")
                    # Don't fail completely, continue with next step
                    if "timeout" in error_msg.lower():
                        result.logs.append(f"  → Element not found or not visible")
                    elif "not attached" in error_msg.lower():
                        result.logs.append(f"  → Element was removed from DOM")
            
            # Determine final status based on success rate
            if successful_steps == len(steps):
                result.status = "success"
                result.message = f"All {successful_steps} steps completed successfully"
            elif successful_steps > 0:
                result.status = "partial"
                result.message = f"Completed {successful_steps}/{len(steps)} steps"
            else:
                result.status = "error"
                result.message = "No steps completed successfully"
            
            # Get final state
            result.final_url = self.page.url
            
            # Take screenshot
            screenshot_dir = "memory/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            import time
            screenshot_path = f"{screenshot_dir}/result_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            result.screenshot_path = screenshot_path
            
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            result.message = f"Execution failed: {str(e)}"
        
        return result

