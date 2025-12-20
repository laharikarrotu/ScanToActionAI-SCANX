"""
Celery Tasks for Background Processing
"""
import sys
import os
import asyncio
import json
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.celery_app import celery_app
from executor.browser_executor import BrowserExecutor, ExecutionResult
from planner.agent_planner import ActionPlan, ActionStep
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='workers.tasks.execute_browser_automation')
def execute_browser_automation(
    self,
    plan_dict: Dict[str, Any],
    url_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute browser automation in background.
    
    This task runs browser automation asynchronously to prevent API timeouts.
    
    Args:
        plan_dict: ActionPlan as dictionary
        url_hint: Optional URL to navigate to first
    
    Returns:
        ExecutionResult as dictionary
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'step': 'initializing', 'progress': 10})
        
        # Convert plan_dict to ActionPlan
        steps = [ActionStep(**step) for step in plan_dict.get('steps', [])]
        plan = ActionPlan(
            task=plan_dict.get('task', 'Process document'),
            steps=steps,
            estimated_time=plan_dict.get('estimated_time')
        )
        
        # Create browser executor
        self.update_state(state='PROGRESS', meta={'step': 'starting_browser', 'progress': 20})
        executor = BrowserExecutor()
        
        # Run async execution
        self.update_state(state='PROGRESS', meta={'step': 'executing', 'progress': 40})
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(executor.execute_plan(plan, url_hint))
            
            # Cleanup
            self.update_state(state='PROGRESS', meta={'step': 'cleaning_up', 'progress': 90})
            loop.run_until_complete(executor.close())
            
            self.update_state(state='PROGRESS', meta={'step': 'complete', 'progress': 100})
            
            # Convert result to dictionary
            return {
                'status': result.status,
                'message': result.message,
                'logs': result.logs,
                'final_url': result.final_url,
                'screenshot_path': result.screenshot_path,
                'error': result.error
            }
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Browser automation task failed: {str(e)}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'step': 'error'}
        )
        return {
            'status': 'error',
            'message': f'Execution failed: {str(e)}',
            'error': str(e)
        }

@celery_app.task(bind=True, name='workers.tasks.extract_prescription_async')
def extract_prescription_async(
    self,
    image_data_base64: str,
    image_hash: str
) -> Dict[str, Any]:
    """
    Extract prescription from image in background.
    
    Args:
        image_data_base64: Base64-encoded image data
        image_hash: MD5 hash of image for caching
    
    Returns:
        PrescriptionInfo as dictionary
    """
    try:
        import base64
        from medication.prescription_extractor import PrescriptionExtractor
        
        self.update_state(state='PROGRESS', meta={'step': 'decoding', 'progress': 10})
        
        # Decode image
        image_data = base64.b64decode(image_data_base64)
        
        self.update_state(state='PROGRESS', meta={'step': 'extracting', 'progress': 30})
        
        # Extract prescription
        extractor = PrescriptionExtractor()
        prescription = extractor.extract_from_image(image_data)
        
        self.update_state(state='PROGRESS', meta={'step': 'complete', 'progress': 100})
        
        return prescription.model_dump()
        
    except Exception as e:
        logger.error(f"Prescription extraction task failed: {str(e)}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'step': 'error'}
        )
        return {
            'status': 'error',
            'message': f'Extraction failed: {str(e)}',
            'error': str(e)
        }

@celery_app.task(bind=True, name='workers.tasks.check_interactions_async')
def check_interactions_async(
    self,
    medications: list,
    allergies: Optional[list] = None
) -> Dict[str, Any]:
    """
    Check drug interactions in background.
    
    Args:
        medications: List of medication dictionaries
        allergies: Optional list of allergies
    
    Returns:
        Interaction check results as dictionary
    """
    try:
        from medication.interaction_checker import InteractionChecker, Medication
        
        self.update_state(state='PROGRESS', meta={'step': 'checking', 'progress': 50})
        
        # Convert to Medication objects
        med_objects = [
            Medication(
                name=med.get('name', ''),
                dosage=med.get('dosage'),
                frequency=med.get('frequency')
            )
            for med in medications
        ]
        
        # Check interactions
        checker = InteractionChecker()
        result = checker.check_interactions(med_objects, allergies or [])
        
        self.update_state(state='PROGRESS', meta={'step': 'complete', 'progress': 100})
        
        return result.model_dump() if hasattr(result, 'model_dump') else result
        
    except Exception as e:
        logger.error(f"Interaction check task failed: {str(e)}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'step': 'error'}
        )
        return {
            'status': 'error',
            'message': f'Interaction check failed: {str(e)}',
            'error': str(e)
        }

