"""
Prescription extraction endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import json
import asyncio
import time
import hashlib

from api.config import settings
from api.dependencies import (
    prescription_extractor, pdf_processor, audit_logger,
    CACHE_AVAILABLE, cache_manager,
    track_llm_api_call, track_prescription_extraction,
    track_cache_hit, track_cache_miss, ErrorHandler,
    rate_limiter, pii_redactor
)
from core.logger import get_logger

logger = get_logger("api.routers.prescription")
router = APIRouter(prefix="/extract-prescription", tags=["prescription"])

@router.post("")
async def extract_prescription_direct(
    request: Request,
    file: UploadFile = File(...),
    stream: bool = Form(False)
):
    """
    FAST DIRECT ENDPOINT: Extract prescription data immediately.
    
    Like ChatGPT - just scan and get medications directly.
    No vision/planner steps, just pure extraction.
    
    **Parameters:**
    - `file`: Image file (prescription, medical form, etc.)
    - `stream`: Enable Server-Sent Events (SSE) for real-time progress updates
    
    **Returns:**
    - `prescription_info`: Extracted medication details (name, dosage, frequency, etc.)
    - `cached`: Whether result was served from cache
    
    **HIPAA Compliance:**
    - All image uploads are logged for audit
    - Images can be encrypted at rest (configurable)
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
        
        # Read file data
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
                    raise HTTPException(status_code=400, detail="PDF conversion failed or PDF is empty")
                
                image_data = pdf_images[0]
                logger.info(f"PDF detected: {len(pdf_images)} pages, processing first page")
                
                if len(pdf_images) > 1:
                    logger.warning(f"PDF has {len(pdf_images)} pages. Only processing first page. Consider using multi-page endpoint.")
            except Exception as e:
                logger.error(f"PDF processing failed: {str(e)}")
                from core.error_handler import ErrorHandler
                user_msg = ErrorHandler.get_user_friendly_error(e)
                raise HTTPException(status_code=400, detail=user_msg)
        else:
            image_data = file_data
        
        # HIPAA Compliance: Log image upload
        client_ip = request.client.host if request.client else "unknown"
        image_hash = hashlib.sha256(image_data).hexdigest()
        audit_logger.log_image_upload(user_id=None, image_hash=image_hash, ip_address=client_ip)
        
        # Check cache first (if available)
        if CACHE_AVAILABLE and cache_manager:
            cached_prescription = cache_manager.get_prescription(image_hash)
            if cached_prescription:
                track_cache_hit("prescription")
                logger.info(f"Cache hit for prescription {image_hash[:8]}...", context={"cache": "hit", "image_hash": image_hash[:8]})
                track_prescription_extraction(True)
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "cached": True,
                        "prescription_info": cached_prescription,
                        "message": "Prescription extracted successfully (cached)"
                    }
                )
            else:
                track_cache_miss("prescription")
        
        # If streaming is requested, use SSE
        if stream:
            async def stream_extraction():
                yield f"data: {json.dumps({'step': 'validating', 'progress': 10, 'message': 'Validating image...'})}\n\n"
                await asyncio.sleep(0.1)
                
                yield f"data: {json.dumps({'step': 'ocr', 'progress': 30, 'message': 'Extracting text from image...'})}\n\n"
                await asyncio.sleep(0.1)
                
                yield f"data: {json.dumps({'step': 'analyzing', 'progress': 60, 'message': 'Analyzing prescription with AI...'})}\n\n"
                
                # Security: Redact PII from image before sending to LLM
                try:
                    from vision.ocr_preprocessor import OCRPreprocessor
                    ocr_preprocessor = OCRPreprocessor(enable_pii_redaction=True)
                    ocr_result = ocr_preprocessor.extract_text(image_data, preprocess=True)
                    
                    if ocr_result.get('pii_detected', False):
                        logger.warning(f"PII detected: {ocr_result.get('pii_count', 0)} instances. Redacting before LLM.")
                        redacted_image, redaction_count = pii_redactor.redact_image(
                            image_data, ocr_text=ocr_result.get('original_text'), use_ocr=True
                        )
                        if redaction_count > 0:
                            image_data = redacted_image
                except Exception as e:
                    logger.warning(f"PII redaction failed: {e}. Proceeding (security risk).")
                
                start_time = time.time()
                try:
                    prescription = prescription_extractor.extract_from_image(image_data)
                    prescription_dict = prescription.model_dump()
                    duration = time.time() - start_time
                    
                    track_llm_api_call("gemini", "gemini-1.5-pro", duration, True)
                    track_prescription_extraction(True)
                    
                    audit_logger.log_prescription_extraction(
                        user_id=None,
                        image_hash=image_hash,
                        ip_address=client_ip
                    )
                    
                    if CACHE_AVAILABLE and cache_manager:
                        cache_ttl = settings.cache_ttl_hours * 3600
                        cache_manager.set_prescription(image_hash, prescription_dict, ttl=cache_ttl)
                    
                    yield f"data: {json.dumps({'step': 'complete', 'progress': 100, 'message': 'Extraction complete', 'prescription_info': prescription_dict})}\n\n"
                except Exception as e:
                    duration = time.time() - start_time
                    track_llm_api_call("gemini", "gemini-1.5-pro", duration, False)
                    track_prescription_extraction(False)
                    ErrorHandler.log_error(e, {"endpoint": "extract-prescription", "streaming": True})
                    yield f"data: {json.dumps({'step': 'error', 'progress': 0, 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                stream_extraction(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # Non-streaming: Direct extraction
        start_time = time.time()
        try:
            prescription = prescription_extractor.extract_from_image(image_data)
            prescription_dict = prescription.model_dump()
            
            # Validate that we got actual data, not just "Unknown"
            if prescription_dict.get('medication_name') == 'Unknown' and 'Error extracting' in str(prescription_dict.get('instructions', '')):
                raise ValueError("Failed to extract prescription data. Please ensure the image is clear and contains a visible prescription.")
            
            duration = time.time() - start_time
            
            track_llm_api_call("gemini", "gemini-1.5-pro", duration, True)
            track_prescription_extraction(True)
            
            audit_logger.log_prescription_extraction(
                user_id=None,
                image_hash=image_hash,
                ip_address=client_ip
            )
            
            if CACHE_AVAILABLE and cache_manager:
                cache_ttl = settings.cache_ttl_hours * 3600
                cache_manager.set_prescription(image_hash, prescription_dict, ttl=cache_ttl)
        except ValueError as e:
            # User-friendly errors
            duration = time.time() - start_time
            track_llm_api_call("gemini", "gemini-1.5-pro", duration, False)
            track_prescription_extraction(False)
            from core.error_handler import ErrorHandler
            user_msg = ErrorHandler.get_user_friendly_error(e)
            raise HTTPException(status_code=400, detail=user_msg)
        except Exception as e:
            duration = time.time() - start_time
            track_llm_api_call("gemini", "gemini-1.5-pro", duration, False)
            track_prescription_extraction(False)
            ErrorHandler.log_error(e, {"endpoint": "extract-prescription"})
            # Sanitize error message for production
            user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
            raise HTTPException(status_code=500, detail=user_friendly_msg)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "prescription_info": prescription_dict,
                "message": "Prescription extracted successfully"
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "extract-prescription"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        raise HTTPException(
            status_code=500,
            detail=user_friendly_msg
        )

