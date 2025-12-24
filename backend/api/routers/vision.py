"""
Vision analysis and browser automation endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
import json
import time
import hashlib
import re

from api.config import settings
from api.dependencies import (
    rate_limiter, pdf_processor, audit_logger, event_logger,
    pii_redactor,
    USE_COMBINED_ANALYZER, combined_analyzer, vision_engine, planner_engine,
    prescription_extractor, CACHE_AVAILABLE, cache_manager,
    CIRCUIT_BREAKER_AVAILABLE, gemini_circuit_breaker
)
from core.monitoring import (
    track_llm_api_call, track_vision_analysis, track_browser_execution
)
from core.error_handler import ErrorHandler
from vision.image_quality import ImageQualityChecker
from executor.browser_executor import BrowserExecutor
from api.routers.helpers import extract_prescription_if_applicable
from core.logger import get_logger

logger = get_logger("api.routers.vision")
router = APIRouter(prefix="", tags=["vision"])

@router.post("/analyze-and-execute")
async def analyze_and_execute(
    request: Request,
    file: UploadFile = File(...),
    intent: str = Form(...),
    context: Optional[str] = Form(None),
    verify_only: bool = Form(False)
):
    """
    Main endpoint: Takes image + intent, analyzes, plans, and executes
    
    **Parameters:**
    - `verify_only`: If True, returns plan for user verification (HITL) without executing
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please try again in a moment. ({remaining} requests remaining)"
        )
    
    try:
        # Validate and sanitize input
        if not intent or not intent.strip():
            raise HTTPException(status_code=400, detail="Intent is required")
        
        intent = intent.strip()
        if len(intent) > settings.max_intent_length:
            raise HTTPException(status_code=400, detail=f"Intent is too long (max {settings.max_intent_length} characters)")
        
        intent = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', intent)
        
        # Security: Validate file size
        file_size_mb = file.size / (1024 * 1024) if file.size else 0
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size_mb:.2f}MB. Maximum allowed: {settings.max_file_size_mb}MB"
            )
        
        # Security: Validate file type
        allowed_content_types = [
            "image/jpeg", "image/jpg", "image/png", "image/webp",
            "application/pdf", "image/heic", "image/heif"
        ]
        if file.content_type and file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(allowed_content_types)}"
            )
        
        # Read and validate file
        file_data = await file.read()
        
        # Security: Validate actual file size after reading (prevent decompression bombs)
        actual_size_mb = len(file_data) / (1024 * 1024)
        if actual_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File too large after processing: {actual_size_mb:.2f}MB. Maximum allowed: {settings.max_file_size_mb}MB"
            )
        
        # Check if it's a PDF
        if pdf_processor.is_pdf(file_data):
            try:
                pdf_images = pdf_processor.pdf_to_images(file_data)
                if not pdf_images:
                    raise HTTPException(status_code=400, detail="PDF conversion failed")
                image_data = pdf_images[0]
                logger.info(f"PDF detected: {len(pdf_images)} pages, processing first page")
            except Exception as e:
                logger.error(f"PDF processing failed: {str(e)}", exc_info=True)
                # Sanitize error message to prevent information disclosure
                from core.error_handler import ErrorHandler
                user_msg = ErrorHandler.get_user_friendly_error(e)
                raise HTTPException(status_code=400, detail=user_msg)
        else:
            image_data = file_data
        
        # HIPAA Compliance: Log image upload
        image_hash = hashlib.sha256(image_data).hexdigest()
        audit_logger.log_image_upload(user_id=None, image_hash=image_hash, ip_address=client_ip)
        
        # Security: Redact PII from image before sending to LLM
        try:
            from vision.ocr_preprocessor import OCRPreprocessor
            ocr_preprocessor = OCRPreprocessor(enable_pii_redaction=True)
            ocr_result = ocr_preprocessor.extract_text(image_data, preprocess=True)
            
            if ocr_result.get('pii_detected', False):
                logger.warning(f"PII detected in image: {ocr_result.get('pii_count', 0)} instances. Redacting before LLM processing.")
                redacted_image, redaction_count = pii_redactor.redact_image(
                    image_data, 
                    ocr_text=ocr_result.get('original_text'),
                    use_ocr=True
                )
                if redaction_count > 0:
                    image_data = redacted_image
                    logger.info(f"Image redacted: {redaction_count} PII regions removed before LLM analysis")
        except Exception as e:
            logger.warning(f"PII redaction failed: {e}. Proceeding with original image (security risk).")
        
        # Check file size
        max_file_size = settings.max_file_size_mb * 1024 * 1024
        if len(file_data) > max_file_size:
            raise HTTPException(status_code=400, detail=f"Image is too large (max {settings.max_file_size_mb}MB)")
        
        # Check file type
        if not file.content_type:
            if not pdf_processor.is_pdf(file_data) and not file_data.startswith(b'\xff\xd8'):
                raise HTTPException(status_code=400, detail="File must be an image or PDF")
        elif not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
            raise HTTPException(status_code=400, detail="File must be an image or PDF")
        
        # Check image quality
        quality_checker = ImageQualityChecker()
        quality_result = quality_checker.validate_image(image_data)
        
        if not quality_result["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail=quality_result["overall_message"]
            )
        
        # Check cache first
        if CACHE_AVAILABLE and cache_manager:
            cached_result = cache_manager.get_ui_schema(image_hash, intent)
            if cached_result:
                logger.info(f"Cache hit for image {image_hash[:8]}...", context={"cache": "hit", "image_hash": image_hash[:8]})
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "ui_schema": cached_result,
                        "cached": True
                    }
                )
        
        # Log request
        event_logger.log_scan_request(image_hash, intent)
        
        # Parse context safely with size limit
        context_dict = None
        if context:
            max_json_size = settings.max_json_size_kb * 1024
            if len(context.encode('utf-8')) > max_json_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Context JSON is too large (max {settings.max_json_size_kb}KB)"
                )
            try:
                context_dict = json.loads(context)
                if not isinstance(context_dict, dict):
                    context_dict = None
            except json.JSONDecodeError:
                context_dict = None
        
        # OPTIMIZATION: Use combined analyzer if available
        ui_schema = None
        plan = None
        ui_schema_dict = None
        plan_dict = None
        used_combined = False
        
        if USE_COMBINED_ANALYZER and combined_analyzer:
            try:
                logger.info("🚀 Using combined analyzer (Vision + Planning in 1 call) - 50% faster & cheaper!")
                
                start_time = time.time()
                def analyze_and_plan_sync():
                    return combined_analyzer.analyze_and_plan(
                        image_data=image_data,
                        user_intent=intent,
                        context=context_dict
                    )
                
                try:
                    if CIRCUIT_BREAKER_AVAILABLE:
                        ui_schema, plan = gemini_circuit_breaker.call(analyze_and_plan_sync)
                    else:
                        ui_schema, plan = analyze_and_plan_sync()
                    duration = time.time() - start_time
                    
                    track_llm_api_call("gemini", "gemini-1.5-pro", duration, True)
                    track_vision_analysis(True)
                    
                    ui_schema_dict = ui_schema.model_dump()
                    plan_dict = plan.model_dump()
                    
                    event_logger.log_ui_schema(ui_schema_dict)
                    event_logger.log_action_plan(plan_dict)
                    
                    if CACHE_AVAILABLE and cache_manager:
                        cache_manager.set_ui_schema(image_hash, intent, ui_schema_dict, ttl=settings.ui_schema_cache_ttl_seconds)
                except Exception as e:
                    duration = time.time() - start_time
                    track_llm_api_call("gemini", "gemini-1.5-pro", duration, False)
                    track_vision_analysis(False)
                    raise
                
                logger.info(f"Combined analysis completed: {len(ui_schema.elements)} elements, {len(plan.steps)} steps (1 API call instead of 2)", context={"elements": len(ui_schema.elements), "steps": len(plan.steps), "optimization": "combined"})
                
                used_combined = True
                
            except Exception as e:
                logger.error(f"Combined analyzer error: {str(e)}", exception=e)
                logger.info("⚠️  Falling back to separate vision + planning calls")
                used_combined = False
        
        # Fallback: Use separate vision and planning calls
        if not used_combined:
            try:
                start_time = time.time()
                def analyze_image_sync():
                    return vision_engine.analyze_image(image_data)
                
                if CIRCUIT_BREAKER_AVAILABLE:
                    ui_schema = gemini_circuit_breaker.call(analyze_image_sync)
                else:
                    ui_schema = analyze_image_sync()
                duration = time.time() - start_time
                
                track_llm_api_call("gemini", "gemini-1.5-pro", duration, True)
                track_vision_analysis(True)
                
                ui_schema_dict = ui_schema.model_dump()
                event_logger.log_ui_schema(ui_schema_dict)
                
                if CACHE_AVAILABLE and cache_manager:
                    cache_manager.set_ui_schema(image_hash, intent, ui_schema_dict, ttl=settings.ui_schema_cache_ttl_seconds)
                
                logger.info(f"Vision analysis completed: {len(ui_schema.elements)} elements found", context={"elements_count": len(ui_schema.elements)})

            except Exception as e:
                duration = time.time() - start_time if 'start_time' in locals() else 0
                track_llm_api_call("gemini", "gemini-1.5-pro", duration, False)
                track_vision_analysis(False)
                logger.error(f"Vision analysis error: {str(e)}", exception=e, context={"endpoint": "analyze-and-execute", "step": "vision"})
                from core.error_handler import ErrorHandler
                user_msg = ErrorHandler.get_user_friendly_error(e)
                raise HTTPException(
                    status_code=500,
                    detail=user_msg
                )
            
            # Step 2: Planning
            plan = planner_engine.create_plan(
                user_intent=intent,
                ui_schema=ui_schema_dict,
                context=context_dict
            )
            plan_dict = plan.model_dump()
            event_logger.log_action_plan(plan_dict)
        
        # Check if we have elements
        if not ui_schema.elements or len(ui_schema.elements) == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_elements",
                    "message": "Could not detect UI elements in the image. Try a clearer image or different angle.",
                    "ui_schema": ui_schema_dict,
                    "debug": "No elements extracted from image or OCR"
                }
            )
        
        logger.info(f"Action plan created: {len(plan.steps)} steps", context={"steps_count": len(plan.steps)})
        for i, step in enumerate(plan.steps):
            logger.debug(f"Step {i+1}: {step.action} on {step.target} - {step.description}")
        
        if not plan.steps:
            logger.warning("Plan created but no steps generated. Elements available: " + str(len(ui_schema.elements)))
            return JSONResponse(
                status_code=200,
                content={
                    "status": "plan_only",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "message": "Plan created but no steps to execute. Please try a more specific intent like 'Fill this form' or 'Extract prescription details'."
                }
            )
        
        # Check if execution is needed
        intent_lower = intent.lower() if intent else ""
        needs_browser = any(word in intent_lower for word in ["fill", "submit", "click", "navigate", "book", "schedule", "complete form"])
        has_browser_actions = any(step.action in ["click", "fill", "select", "navigate", "submit"] for step in plan.steps)
        
        # If all steps are "read" actions, skip browser execution
        if not needs_browser and not has_browser_actions:
            extracted_data = {}
            for elem in ui_schema.elements:
                if elem.type in ["medication", "dosage", "prescriber", "pharmacy", "data", "text"]:
                    extracted_data[elem.id] = {
                        "type": elem.type,
                        "label": elem.label,
                        "value": elem.value or elem.label
                    }
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "extracted_data": extracted_data,
                    "message": f"Successfully extracted {len(extracted_data)} data points from the document. No browser execution needed for read-only operations."
                }
            )
        
        # HITL: If verify_only is True, return plan for user verification
        if verify_only:
            extracted_data = {}
            for elem in ui_schema.elements:
                extracted_data[elem.id] = {
                    "type": elem.type,
                    "label": elem.label,
                    "value": elem.value or None,
                    "position": elem.position
                }
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "verification_required",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "extracted_data": extracted_data,
                    "message": "Please verify and edit the extracted data before execution. This helps ensure 100% accuracy for medical forms."
                }
            )
        
        # Step 3: Execution
        # Parse allowed domains for SSRF protection
        from api.config import settings
        allowed_domains_list = None
        if settings.allowed_domains:
            allowed_domains_list = [domain.strip() for domain in settings.allowed_domains.split(",") if domain.strip()]
        executor = BrowserExecutor(headless=True, allowed_domains=allowed_domains_list)
        try:
            start_url = ui_schema.url_hint
            
            if start_url:
                if not (start_url.startswith("http://") or start_url.startswith("https://")):
                    start_url = None
            
            if not start_url:
                extracted_data = {}
                
                structured_data = await extract_prescription_if_applicable(
                    image_data, ui_schema, intent_lower, prescription_extractor, logger
                )
                
                for elem in ui_schema.elements:
                    elem_type = elem.type if hasattr(elem, 'type') else elem.get("type", "")
                    elem_label = elem.label if hasattr(elem, 'label') else elem.get("label", "")
                    elem_value = elem.value if hasattr(elem, 'value') else elem.get("value", "")
                    
                    if elem_type in ["medication", "dosage", "prescriber", "pharmacy", "data", "text"]:
                        extracted_data[elem.id] = {
                            "type": elem_type,
                            "label": elem_label,
                            "value": elem_value or elem_label
                        }
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "ui_schema": ui_schema_dict,
                        "plan": plan_dict,
                        "extracted_data": extracted_data,
                        "structured_data": structured_data if structured_data else None,
                        "message": f"Document analyzed. Extracted {len(extracted_data)} data points. For form filling, please provide a URL or upload a form that can be filled online."
                    }
                )
            
            exec_start_time = time.time()
            try:
                result = await executor.execute_plan(
                    steps=plan.steps,
                    ui_schema=ui_schema_dict,
                    start_url=start_url
                )
                exec_duration = time.time() - exec_start_time
                track_browser_execution(True, exec_duration)
                
                result_dict = result.model_dump()
                event_logger.log_execution_result(result_dict)
            except Exception as e:
                exec_duration = time.time() - exec_start_time
                track_browser_execution(False, exec_duration)
                raise
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": result.status,
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "execution": result_dict,
                    "message": result.message
                }
            )
        except Exception as exec_error:
            logger.error(f"Browser execution error: {str(exec_error)}", exception=exec_error, context={"endpoint": "analyze-and-execute", "step": "browser_execution"})
            
            extracted_data = {}
            structured_data = {}
            
            structured_data = await extract_prescription_if_applicable(
                image_data, ui_schema, intent_lower, prescription_extractor, logger
            )
            
            for elem in ui_schema.elements:
                elem_type = elem.type if hasattr(elem, 'type') else elem.get("type", "")
                elem_label = elem.label if hasattr(elem, 'label') else elem.get("label", "")
                elem_value = elem.value if hasattr(elem, 'value') else elem.get("value", "")
                
                if elem_type in ["medication", "dosage", "prescriber", "pharmacy", "data", "text"]:
                    extracted_data[elem.id] = {
                        "type": elem_type,
                        "label": elem_label,
                        "value": elem_value or elem_label
                    }
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "partial",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "extracted_data": extracted_data,
                    "structured_data": structured_data if structured_data else None,
                    "message": f"Browser execution failed (likely no website to interact with). Extracted {len(extracted_data)} data points from the document instead."
                }
            )
        finally:
            try:
                await executor.close()
            except Exception as cleanup_error:
                logger.warning(f"Browser executor cleanup error: {cleanup_error}", exception=cleanup_error)
            
    except HTTPException:
        raise
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "analyze-and-execute"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        event_logger.log_event("error", {"error": str(e), "endpoint": "analyze-and-execute"})
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg,
                "error_type": type(e).__name__
            }
        )

@router.post("/execute-verified-plan")
async def execute_verified_plan_endpoint(
    request: Request,
    verified_plan: str = Form(...),
    verified_data: str = Form(...),
    ui_schema: str = Form(...),
    start_url: str = Form(...)
):
    """HITL: Execute a plan after user verification and editing."""
    try:
        from api.execute_verified import execute_verified_plan
        
        # Security: Validate JSON size before parsing
        max_json_size = settings.max_json_size_kb * 1024
        
        if len(verified_plan.encode('utf-8')) > max_json_size:
            raise HTTPException(status_code=400, detail=f"Verified plan JSON too large (max {settings.max_json_size_kb}KB)")
        if len(verified_data.encode('utf-8')) > max_json_size:
            raise HTTPException(status_code=400, detail=f"Verified data JSON too large (max {settings.max_json_size_kb}KB)")
        if len(ui_schema.encode('utf-8')) > max_json_size:
            raise HTTPException(status_code=400, detail=f"UI schema JSON too large (max {settings.max_json_size_kb}KB)")
        
        plan_dict = json.loads(verified_plan)
        data_dict = json.loads(verified_data)
        schema_dict = json.loads(ui_schema)
        
        if not isinstance(plan_dict, dict) or not isinstance(data_dict, dict) or not isinstance(schema_dict, dict):
            raise HTTPException(status_code=400, detail="Invalid JSON structure")
        
        result = await execute_verified_plan(
            verified_plan=plan_dict,
            verified_data=data_dict,
            ui_schema=schema_dict,
            start_url=start_url
        )
        
        result_dict = result.model_dump()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": result.status,
                "message": result.message,
                "execution": result_dict,
                "verified": True
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "execute-verified-plan"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

