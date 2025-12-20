"""
Comprehensive E2E Test Suite for HealthScan

Tests the complete "See-Think-Act" pipeline:
1. Vision: Image analysis and UI element detection
2. Planning: Action plan generation
3. Execution: Browser automation
4. Integration: Prescription extraction, interactions, diet recommendations
"""
import pytest
import asyncio
import os
import sys
import base64
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from playwright.async_api import async_playwright, Page, Browser
from vision.ui_detector import VisionEngine, UISchema
from planner.agent_planner import PlannerEngine, ActionPlan
from executor.browser_executor import BrowserExecutor, ExecutionResult
from medication.prescription_extractor import PrescriptionExtractor
from medication.interaction_checker import InteractionChecker, Medication
from nutrition.diet_advisor import DietAdvisor

# Test configuration
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def browser():
    """Create browser instance for tests"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser: Browser):
    """Create a new page for each test"""
    page = await browser.new_page()
    yield page
    await page.close()

class TestVisionEngine:
    """Test Vision Engine - Image Analysis"""
    
    @pytest.mark.asyncio
    async def test_vision_engine_initialization(self):
        """Test that VisionEngine can be initialized"""
        engine = VisionEngine()
        assert engine is not None
        assert engine.model == "gpt-4o"
    
    @pytest.mark.asyncio
    async def test_image_analysis_basic(self):
        """Test basic image analysis"""
        # Create a simple test image (1x1 pixel)
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        image_data = img_bytes.getvalue()
        
        engine = VisionEngine()
        try:
            schema = engine.analyze_image(image_data)
            assert schema is not None
            assert isinstance(schema, UISchema)
            assert schema.page_type is not None
        except Exception as e:
            # If API key not set, skip test
            if "API key" in str(e) or "OpenAI" in str(e):
                pytest.skip("OpenAI API key not configured")
            raise

class TestPlannerEngine:
    """Test Planner Engine - Action Plan Generation"""
    
    @pytest.mark.asyncio
    async def test_planner_initialization(self):
        """Test that PlannerEngine can be initialized"""
        planner = PlannerEngine()
        assert planner is not None
    
    @pytest.mark.asyncio
    async def test_plan_creation_with_elements(self):
        """Test plan creation with UI elements"""
        planner = PlannerEngine()
        
        ui_schema = {
            "page_type": "medical_form",
            "elements": [
                {"id": "name_field", "type": "input", "label": "Patient Name"},
                {"id": "submit_button", "type": "button", "label": "Submit"}
            ]
        }
        
        try:
            plan = planner.create_plan("Fill this form", ui_schema)
            assert plan is not None
            assert isinstance(plan, ActionPlan)
            assert len(plan.steps) > 0
        except Exception as e:
            if "API key" in str(e):
                pytest.skip("OpenAI API key not configured")
            raise
    
    @pytest.mark.asyncio
    async def test_planner_fallback_logic(self):
        """Test that planner creates fallback steps when LLM fails"""
        planner = PlannerEngine()
        
        ui_schema = {
            "page_type": "prescription",
            "elements": [
                {"id": "med1", "type": "medication", "label": "Aspirin"},
                {"id": "dosage1", "type": "dosage", "label": "100mg"}
            ]
        }
        
        # Even with invalid API key, should create fallback steps
        plan = planner.create_plan("Read prescription", ui_schema)
        assert plan is not None
        assert len(plan.steps) > 0

class TestBrowserExecutor:
    """Test Browser Executor - Automation"""
    
    @pytest.mark.asyncio
    async def test_browser_executor_initialization(self):
        """Test that BrowserExecutor can be initialized"""
        executor = BrowserExecutor()
        assert executor is not None
        
        # Cleanup
        await executor.close()
    
    @pytest.mark.asyncio
    async def test_browser_cleanup(self):
        """Test that browser resources are properly cleaned up"""
        executor = BrowserExecutor()
        
        # Verify browser is created
        assert executor.browser is None  # Not created until execute_plan
        
        # Create a simple plan
        plan = ActionPlan(
            task="Test task",
            steps=[],
            estimated_time=1
        )
        
        # Execute (will fail but should cleanup)
        try:
            await executor.execute_plan(plan, "https://example.com")
        except:
            pass  # Expected to fail
        
        # Cleanup
        await executor.close()
        
        # Verify cleanup
        assert executor.browser is None
        assert executor.context is None
        assert executor.page is None

class TestPrescriptionExtraction:
    """Test Prescription Extraction"""
    
    @pytest.mark.asyncio
    async def test_prescription_extractor_initialization(self):
        """Test PrescriptionExtractor initialization"""
        extractor = PrescriptionExtractor()
        assert extractor is not None
    
    @pytest.mark.skip(reason="Requires actual prescription image")
    async def test_prescription_extraction(self):
        """Test prescription extraction from image"""
        # This test requires a real prescription image
        extractor = PrescriptionExtractor()
        
        # Load test image if available
        test_image_path = TEST_IMAGES_DIR / "prescription.jpg"
        if not test_image_path.exists():
            pytest.skip("Test prescription image not found")
        
        with open(test_image_path, "rb") as f:
            image_data = f.read()
        
        try:
            prescription = extractor.extract_from_image(image_data)
            assert prescription is not None
            assert prescription.medication_name is not None
        except Exception as e:
            if "API key" in str(e):
                pytest.skip("OpenAI API key not configured")
            raise

class TestIntegration:
    """Integration Tests - Full Pipeline"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self):
        """Test the complete See-Think-Act pipeline"""
        # This is a comprehensive test that verifies the entire flow
        
        # Step 1: Vision
        vision_engine = VisionEngine()
        
        # Create test image
        from PIL import Image
        import io
        img = Image.new('RGB', (200, 200), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        image_data = img_bytes.getvalue()
        
        try:
            # Step 1: Analyze image
            ui_schema = vision_engine.analyze_image(image_data)
            assert ui_schema is not None
            
            # Step 2: Create plan
            planner = PlannerEngine()
            plan = planner.create_plan("Read document", ui_schema.model_dump())
            assert plan is not None
            assert len(plan.steps) > 0
            
            # Step 3: Execute (if URL available)
            if ui_schema.url_hint:
                executor = BrowserExecutor()
                try:
                    result = await executor.execute_plan(plan, ui_schema.url_hint)
                    assert result is not None
                finally:
                    await executor.close()
        except Exception as e:
            if "API key" in str(e):
                pytest.skip("API keys not configured")
            raise

class TestAPIEndpoints:
    """Test API Endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Backend server not running")
    
    @pytest.mark.asyncio
    async def test_image_quality_endpoint(self):
        """Test image quality check endpoint"""
        import httpx
        from PIL import Image
        import io
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        
        async with httpx.AsyncClient() as client:
            try:
                files = {'file': ('test.jpg', image_data, 'image/jpeg')}
                response = await client.post(
                    f"{API_BASE_URL}/check-image-quality",
                    files=files,
                    timeout=10.0
                )
                assert response.status_code == 200
                data = response.json()
                assert 'is_valid' in data
                assert 'score' in data
            except httpx.ConnectError:
                pytest.skip("Backend server not running")

@pytest.mark.asyncio
async def test_browser_memory_leak():
    """Test that browser executor doesn't leak memory"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_children = len(process.children(recursive=True))
    
    # Create and close multiple executors
    for _ in range(5):
        executor = BrowserExecutor()
        await executor.close()
    
    # Wait a bit for cleanup
    await asyncio.sleep(2)
    
    final_children = len(process.children(recursive=True))
    
    # Should not have significantly more child processes
    assert final_children <= initial_children + 2, "Possible memory leak detected"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

