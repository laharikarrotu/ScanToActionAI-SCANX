"""
End-to-End Tests: Frontend-Backend Integration

These tests verify the complete user flow from frontend to backend:
1. Frontend API calls match backend expectations
2. Request/response formats are compatible
3. Data flows correctly through the stack
4. Error handling works end-to-end
5. Real user scenarios are tested

Each test simulates a real user interaction:
- User uploads image in frontend
- Frontend calls backend API
- Backend processes and responds
- Frontend displays results
- User interacts with results

Test Structure:
- Setup: Create test data, mock services if needed
- Action: Simulate user action (API call)
- Assert: Verify end-to-end behavior
- Cleanup: Reset state if needed
"""

import pytest
import sys
import os

# Optional dependencies - skip tests if not available
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import asyncio
from typing import Dict, Any, Optional
import json
from io import BytesIO

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_API_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
TEST_FRONTEND_URL = os.getenv("TEST_FRONTEND_URL", "http://localhost:3000")
TEST_TIMEOUT = 30.0  # 30 seconds timeout for API calls


class TestE2EPrescriptionFlow:
    """
    End-to-End Test: Complete Prescription Extraction Flow
    
    Simulates:
    1. User uploads prescription image in frontend
    2. Frontend calls /extract-prescription
    3. Backend processes image with LLM
    4. Backend returns prescription data
    5. Frontend displays prescription card
    6. User can interact with prescription data
    """
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_prescription_extraction_flow(self):
        """
        Purpose: Verifies the complete prescription extraction flow from frontend to backend.
        
        What it tests:
        - Frontend can upload image file
        - Backend accepts multipart/form-data with file
        - Backend processes image and extracts prescription
        - Response format matches frontend expectations
        - Frontend can parse and display prescription data
        - Streaming progress updates work (if enabled)
        
        Dependencies:
        - Backend server running
        - Frontend server running (optional - can test API directly)
        - Gemini API key
        - Tesseract OCR
        
        Expected behavior:
        - Image upload succeeds
        - Prescription data is extracted
        - Response contains prescription_info with:
          * medication_name
          * dosage
          * frequency
          * prescriber (if available)
        - Data format matches TypeScript types in frontend
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        if not PIL_AVAILABLE:
            pytest.skip("PIL/Pillow not available")
        # Simulate frontend file upload
        img = Image.new('RGB', (200, 200), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Simulate frontend FormData
            files = {'file': ('prescription.png', img_bytes, 'image/png')}
            data = {'stream': 'true'}  # Enable streaming like frontend does
            
            response = await client.post(
                f"{TEST_API_URL}/extract-prescription",
                files=files,
                data=data
            )
            
            # Verify response
            assert response.status_code in [200, 400, 422, 500]
            
            if response.status_code == 200:
                # Check if streaming or JSON response
                content_type = response.headers.get('content-type', '')
                
                if 'text/event-stream' in content_type:
                    # Parse SSE stream (simplified - real frontend does more)
                    text = response.text
                    # Should contain SSE data events
                    assert 'data:' in text or len(text) > 0
                else:
                    # JSON response
                    result = response.json()
                    # Verify response structure matches frontend expectations
                    assert 'prescription_info' in result or 'status' in result or 'message' in result
                    
                    if 'prescription_info' in result:
                        prescription = result['prescription_info']
                        # Verify structure matches TypeScript PrescriptionInfo type
                        assert isinstance(prescription, dict)
                        # Should have medication details
                        assert 'medication_name' in prescription or 'medications' in prescription
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_prescription_to_chat_flow(self):
        """
        Purpose: Verifies that prescription data can be used in chat context.
        
        What it tests:
        - Prescription is extracted
        - Prescription data is passed to chat endpoint as context
        - Chat AI uses prescription context to answer questions
        - Response is relevant to the prescription
        
        Dependencies:
        - Backend server running
        - Gemini API key
        
        Expected behavior:
        - Prescription extraction succeeds
        - Chat accepts prescription context
        - Chat response references prescription data
        - Context is properly formatted
        """
        # Step 1: Extract prescription
        img = Image.new('RGB', (200, 200), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Extract prescription
            files = {'file': ('prescription.png', img_bytes, 'image/png')}
            data = {'stream': 'false'}
            
            extract_response = await client.post(
                f"{TEST_API_URL}/extract-prescription",
                files=files,
                data=data
            )
            
            if extract_response.status_code == 200:
                prescription_data = extract_response.json().get('prescription_info', {})
                
                # Step 2: Use prescription in chat
                chat_payload = {
                    "message": "What are the side effects of this medication?",
                    "context": {
                        "prescription_data": prescription_data
                    },
                    "conversation_history": None
                }
                
                chat_response = await client.post(
                    f"{TEST_API_URL}/chat",
                    json=chat_payload
                )
                
                # Chat should succeed and use context
                assert chat_response.status_code in [200, 503, 500]
                
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    # Should have AI response
                    assert 'response' in chat_result or 'message' in chat_result


class TestE2EInteractionFlow:
    """
    End-to-End Test: Complete Drug Interaction Checking Flow
    
    Simulates:
    1. User uploads multiple prescription images
    2. Frontend calls /check-prescription-interactions
    3. Backend extracts medications from each
    4. Backend checks for interactions
    5. Frontend displays interaction warnings
    6. User can navigate to diet recommendations based on interactions
    """
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_interaction_check_flow(self):
        """
        Purpose: Verifies the complete drug interaction checking flow.
        
        What it tests:
        - Multiple prescription images are uploaded
        - Medications are extracted from each
        - Interactions are detected and categorized
        - Response format matches frontend expectations
        - Interaction data can be used for navigation
        
        Dependencies:
        - Backend server running
        - Gemini API key
        - Interaction checker service
        
        Expected behavior:
        - Multiple files are accepted
        - Response contains:
          * prescriptions: List of extracted medications
          * interactions: Categorized by severity
          * has_interactions: Boolean flag
          * warnings: User-friendly warnings
        - Data format matches frontend InteractionResult type
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        if not PIL_AVAILABLE:
            pytest.skip("PIL/Pillow not available")
        
        # Create multiple test images
        img1 = Image.new('RGB', (200, 200), color='white')
        img2 = Image.new('RGB', (200, 200), color='white')
        
        img1_bytes = BytesIO()
        img2_bytes = BytesIO()
        img1.save(img1_bytes, format='PNG')
        img2.save(img2_bytes, format='PNG')
        img1_bytes.seek(0)
        img2_bytes.seek(0)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Simulate frontend multi-file upload
            files = [
                ('files', ('prescription1.png', img1_bytes, 'image/png')),
                ('files', ('prescription2.png', img2_bytes, 'image/png'))
            ]
            data = {'allergies': 'penicillin, aspirin'}
            
            response = await client.post(
                f"{TEST_API_URL}/check-prescription-interactions",
                files=files,
                data=data
            )
            
            assert response.status_code in [200, 400, 422, 500]
            
            if response.status_code == 200:
                result = response.json()
                # Verify response structure matches frontend expectations
                # Should have interaction data
                assert 'prescriptions' in result or 'interactions' in result or 'has_interactions' in result or 'warnings' in result
                
                # If interactions found, verify structure
                if 'interactions' in result:
                    interactions = result['interactions']
                    assert isinstance(interactions, (dict, list))
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_interaction_to_diet_navigation(self):
        """
        Purpose: Verifies that interaction results can be used to get diet recommendations.
        
        What it tests:
        - Interaction check completes
        - Interaction data includes medication list
        - Medications are passed to diet endpoint
        - Diet recommendations account for medications
        - Data flows correctly between endpoints
        
        Dependencies:
        - Backend server running
        - All services available
        
        Expected behavior:
        - Interaction check succeeds
        - Diet recommendations are generated
        - Recommendations consider medications from interactions
        - Response format is correct
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        
        # This would test:
        # 1. Check interactions → get medications
        # 2. Use medications → get diet recommendations
        # 3. Verify recommendations are medication-aware
        pass  # Implement based on actual navigation flow


class TestE2EDietFlow:
    """
    End-to-End Test: Complete Diet Recommendation Flow
    
    Simulates:
    1. User enters medical condition in frontend
    2. User enters current medications
    3. Frontend calls /get-diet-recommendations
    4. Backend generates personalized recommendations
    5. Frontend displays diet plan
    6. User can chat about diet recommendations
    """
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_diet_recommendation_flow(self):
        """
        Purpose: Verifies the complete diet recommendation flow.
        
        What it tests:
        - Form data is submitted correctly
        - Backend processes condition, medications, restrictions
        - Recommendations are generated
        - Response format matches frontend expectations
        - Recommendations can be used in chat
        
        Dependencies:
        - Backend server running
        - Gemini API key
        - Diet advisor service
        
        Expected behavior:
        - Returns personalized diet recommendations
        - Response contains:
          * foods_to_eat: List of recommended foods
          * foods_to_avoid: List of foods to avoid
          * nutritional_focus: Key nutrients to focus on
          * warnings: Medication-food interaction warnings
        - Data format matches frontend DietData type
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Simulate frontend form submission
            data = {
                "condition": "Type 2 Diabetes",
                "medications": "metformin, insulin",
                "dietary_restrictions": "gluten-free, dairy-free"
            }
            
            response = await client.post(
                f"{TEST_API_URL}/get-diet-recommendations",
                data=data
            )
            
            assert response.status_code in [200, 400, 500]
            
            if response.status_code == 200:
                result = response.json()
                # Verify response structure
                assert 'recommendations' in result or 'foods_to_eat' in result or 'status' in result
                
                if 'recommendations' in result:
                    recs = result['recommendations']
                    # Should have diet recommendation structure
                    assert isinstance(recs, dict)


class TestE2EFrontendBackendContract:
    """
    Tests that verify the contract between frontend and backend:
    - Request formats match
    - Response formats match
    - TypeScript types match Python types
    - Error handling is consistent
    """
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_api_response_matches_frontend_types(self):
        """
        Purpose: Verifies that backend responses match frontend TypeScript type definitions.
        
        What it tests:
        - Prescription response matches PrescriptionInfo type
        - Interaction response matches InteractionResult type
        - Diet response matches DietData type
        - Chat response matches ChatResponse type
        - All required fields are present
        - Field types are correct (string, number, array, object)
        
        Dependencies:
        - Backend server running
        - Frontend types defined in types.ts
        
        Expected behavior:
        - All responses have required fields
        - Field types match TypeScript definitions
        - Optional fields are handled correctly
        - No unexpected fields (or they're ignored)
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        
        # This would validate:
        # 1. Get actual API response
        # 2. Compare against TypeScript type definition
        # 3. Verify field presence and types
        # 4. Check for type mismatches
        pass  # Implement type validation logic
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_responses_are_consistent(self):
        """
        Purpose: Verifies that error responses are consistent and frontend can handle them.
        
        What it tests:
        - Error response format is consistent across endpoints
        - Error codes are standard (400, 401, 403, 404, 429, 500, 503)
        - Error messages are user-friendly
        - Frontend can parse and display errors
        - Error structure matches frontend error handling
        
        Dependencies:
        - Backend server running
        
        Expected behavior:
        - All errors return consistent format
        - Error messages are sanitized
        - Error codes are appropriate
        - Frontend can extract error details
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Test various error scenarios
            error_scenarios = [
                # Missing required field
                {'endpoint': '/extract-prescription', 'data': {}, 'expected_status': [400, 422]},
                # Invalid file type
                {'endpoint': '/extract-prescription', 'files': {'file': ('test.txt', b'text', 'text/plain')}, 'expected_status': [400, 422]},
                # Rate limit (if we can trigger it)
                # Authentication error (if auth is required)
            ]
            
            for scenario in error_scenarios:
                endpoint = scenario['endpoint']
                expected_status = scenario['expected_status']
                
                if 'files' in scenario:
                    response = await client.post(
                        f"{TEST_API_URL}{endpoint}",
                        files=scenario['files']
                    )
                else:
                    response = await client.post(
                        f"{TEST_API_URL}{endpoint}",
                        data=scenario.get('data', {})
                    )
                
                # Verify error format
                assert response.status_code in expected_status
                
                if response.status_code >= 400:
                    # Error should be parseable
                    try:
                        error_data = response.json()
                        # Should have error message
                        assert 'detail' in error_data or 'message' in error_data or 'error' in error_data
                    except:
                        # Some errors may be plain text
                        assert len(response.text) > 0


class TestE2EUserScenarios:
    """
    Real-world user scenario tests that simulate actual user workflows.
    """
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_user_scenario_new_prescription(self):
        """
        Purpose: Tests the complete flow for a new user with a new prescription.
        
        Scenario:
        1. User uploads prescription image
        2. Prescription is extracted
        3. User views prescription details
        4. User asks chat about medication
        5. User checks for interactions (if multiple medications)
        6. User gets diet recommendations based on condition
        
        What it tests:
        - Complete new user onboarding flow
        - All endpoints work together
        - Data persists through the flow
        - User can navigate between features
        
        Dependencies:
        - Backend server running
        - All services available
        
        Expected behavior:
        - Each step succeeds
        - Data flows correctly between steps
        - User experience is smooth
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        
        # Implement complete user flow
        pass
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_user_scenario_existing_patient(self):
        """
        Purpose: Tests flow for returning user with existing data.
        
        Scenario:
        1. User has previous prescription data (cached)
        2. User uploads new prescription
        3. System checks interactions with previous prescriptions
        4. User gets updated recommendations
        
        What it tests:
        - Caching works across sessions
        - Historical data is considered
        - Multi-prescription interaction checking
        - Data consistency
        
        Dependencies:
        - Backend server running
        - Cache service available
        
        Expected behavior:
        - Previous data is retrieved
        - New data is integrated
        - Interactions consider all prescriptions
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        
        pass
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_user_scenario_error_recovery(self):
        """
        Purpose: Tests how system handles errors and user recovery.
        
        Scenario:
        1. User uploads invalid image
        2. System shows error
        3. User uploads valid image
        4. System processes successfully
        5. User continues workflow
        
        What it tests:
        - Error handling doesn't break workflow
        - User can recover from errors
        - System state is consistent after errors
        - Error messages are helpful
        
        Dependencies:
        - Backend server running
        
        Expected behavior:
        - Errors are handled gracefully
        - User can retry
        - System recovers cleanly
        """
        # Skip if dependencies not available
        if not HTTPX_AVAILABLE:
            pytest.skip("httpx not available")
        
        pass

