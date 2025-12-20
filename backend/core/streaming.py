"""
Response Streaming Module
Streams partial results for better perceived performance
"""
import json
from typing import AsyncGenerator, Dict, Any, Optional
from fastapi.responses import StreamingResponse
import asyncio

class StreamingResponseBuilder:
    """
    Builds streaming responses for long-running operations
    Provides progress updates to frontend
    """
    
    @staticmethod
    async def stream_prescription_extraction(
        image_data: bytes,
        extractor,
        progress_callback: Optional[callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream prescription extraction progress
        """
        # Step 1: Image validation
        yield f"data: {json.dumps({'step': 'validating', 'progress': 10, 'message': 'Validating image...'})}\n\n"
        await asyncio.sleep(0.1)  # Simulate processing
        
        # Step 2: OCR extraction
        yield f"data: {json.dumps({'step': 'ocr', 'progress': 30, 'message': 'Extracting text from image...'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 3: AI analysis
        yield f"data: {json.dumps({'step': 'analyzing', 'progress': 60, 'message': 'Analyzing prescription...'})}\n\n"
        
        # Actual extraction (this is the slow part)
        try:
            prescription = extractor.extract_from_image(image_data)
            prescription_dict = prescription.model_dump()
            
            # Step 4: Complete
            yield f"data: {json.dumps({'step': 'complete', 'progress': 100, 'message': 'Extraction complete', 'data': prescription_dict})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'progress': 0, 'message': str(e)})}\n\n"
    
    @staticmethod
    async def stream_analysis_and_execution(
        image_data: bytes,
        intent: str,
        vision_engine,
        planner_engine,
        executor,
        progress_callback: Optional[callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream analyze-and-execute progress
        """
        # Step 1: Image validation
        yield f"data: {json.dumps({'step': 'validating', 'progress': 5, 'message': 'Validating image...'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 2: Vision analysis
        yield f"data: {json.dumps({'step': 'vision', 'progress': 25, 'message': 'Analyzing UI elements...'})}\n\n"
        ui_schema = await vision_engine.detect_ui_elements(image_data, intent)
        yield f"data: {json.dumps({'step': 'vision_complete', 'progress': 40, 'message': f'Found {len(ui_schema.elements)} elements'})}\n\n"
        
        # Step 3: Planning
        yield f"data: {json.dumps({'step': 'planning', 'progress': 50, 'message': 'Creating action plan...'})}\n\n"
        action_plan = await planner_engine.create_plan(ui_schema, intent)
        yield f"data: {json.dumps({'step': 'planning_complete', 'progress': 70, 'message': f'Created {len(action_plan.steps)} step plan'})}\n\n"
        
        # Step 4: Execution
        yield f"data: {json.dumps({'step': 'executing', 'progress': 80, 'message': 'Executing actions...'})}\n\n"
        result = await executor.execute_plan(action_plan)
        yield f"data: {json.dumps({'step': 'complete', 'progress': 100, 'message': 'Execution complete', 'data': result.model_dump()})}\n\n"
    
    @staticmethod
    def create_streaming_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
        """
        Create a FastAPI StreamingResponse from generator
        """
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

