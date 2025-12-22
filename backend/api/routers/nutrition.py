"""
Nutrition and diet recommendation endpoints
"""
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import re

from api.config import settings
from api.dependencies import (
    diet_advisor, CACHE_AVAILABLE, cache_manager
)
from core.error_handler import ErrorHandler
from core.logger import get_logger

logger = get_logger("api.routers.nutrition")
router = APIRouter(prefix="", tags=["nutrition"])

@router.post("/get-diet-recommendations")
async def get_diet_recommendations(
    condition: str = Form(...),
    medications: Optional[str] = Form(None),
    dietary_restrictions: Optional[str] = Form(None)
):
    """
    Get personalized diet recommendations based on medical condition.
    
    **Parameters:**
    - `condition`: Medical condition/diagnosis (e.g., "Type 2 Diabetes")
    - `medications`: Comma-separated list of current medications (optional)
    - `dietary_restrictions`: Comma-separated dietary restrictions (optional)
    
    **Returns:**
    - `recommendations`: Foods to eat, avoid, nutritional focus, warnings
    """
    # Input validation and sanitization
    condition = condition.strip()[:200]
    if not condition:
        raise HTTPException(status_code=400, detail="Condition is required")
    condition = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', condition)
    
    if medications:
        medications = medications.strip()[:500]
        medications = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', medications)
    
    if dietary_restrictions:
        dietary_restrictions = dietary_restrictions.strip()[:500]
        dietary_restrictions = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', dietary_restrictions)
    
    try:
        med_str = medications or ""
        diet_res_str = dietary_restrictions or ""
        
        # Check cache first
        if CACHE_AVAILABLE and cache_manager:
            cached_recommendations = cache_manager.get_diet_recommendations(condition, med_str, diet_res_str)
            if cached_recommendations:
                logger.info(f"Cache hit for diet recommendations: {condition}", context={"cache": "hit", "condition": condition})
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "recommendations": cached_recommendations,
                        "cached": True
                    }
                )
        
        med_list = [m.strip() for m in medications.split(",")] if medications else None
        restrictions_list = [r.strip() for r in dietary_restrictions.split(",")] if dietary_restrictions else None
        
        recommendation = diet_advisor.get_diet_recommendations(
            condition=condition,
            medications=med_list,
            dietary_restrictions=restrictions_list
        )
        recommendation_dict = recommendation.model_dump()
        
        # Cache the result
        if CACHE_AVAILABLE and cache_manager:
            cache_ttl = settings.cache_ttl_hours * 3600
            cache_manager.set_diet_recommendations(condition, med_str, diet_res_str, recommendation_dict, ttl=cache_ttl)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "recommendations": recommendation_dict
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "get-diet-recommendations"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

@router.post("/check-food-compatibility")
async def check_food_compatibility(
    food_item: str = Form(...),
    condition: Optional[str] = Form(None),
    medications: Optional[str] = Form(None)
):
    """
    Check if a food item is compatible with condition/medications.
    
    **Parameters:**
    - `food_item`: Food item to check (e.g., "Grapefruit")
    - `condition`: Medical condition (optional)
    - `medications`: Comma-separated medications (optional)
    
    **Returns:**
    - `compatibility`: Safety status, warnings, recommendations
    """
    # Input validation and sanitization
    food_item = food_item.strip()[:100]
    if not food_item:
        raise HTTPException(status_code=400, detail="Food item is required")
    food_item = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', food_item)
    
    if condition:
        condition = condition.strip()[:200]
        condition = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', condition)
    
    if medications:
        medications = medications.strip()[:500]
        medications = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', medications)
    
    try:
        med_list = [m.strip() for m in medications.split(",")] if medications else None
        
        compatibility = diet_advisor.check_food_compatibility(
            food_item=food_item,
            condition=condition,
            medications=med_list
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "compatibility": compatibility
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "check-food-compatibility"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

@router.post("/generate-meal-plan")
async def generate_meal_plan(
    condition: str = Form(...),
    days: int = Form(7),
    dietary_restrictions: Optional[str] = Form(None)
):
    """
    Generate a personalized meal plan for a medical condition.
    
    **Parameters:**
    - `condition`: Medical condition/diagnosis
    - `days`: Number of days for meal plan (default: 7)
    - `dietary_restrictions`: Comma-separated restrictions (optional)
    
    **Returns:**
    - `meal_plan`: Daily meal plan with breakfast, lunch, dinner, snacks
    - `shopping_list`: Ingredients needed
    - `nutritional_summary`: Calorie and nutrient breakdown
    """
    # Input validation and sanitization
    condition = condition.strip()[:200]
    if not condition:
        raise HTTPException(status_code=400, detail="Condition is required")
    condition = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', condition)
    
    # Validate days (1-30)
    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 30")
    
    if dietary_restrictions:
        dietary_restrictions = dietary_restrictions.strip()[:500]
        dietary_restrictions = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', dietary_restrictions)
    
    try:
        restrictions_list = [r.strip() for r in dietary_restrictions.split(",")] if dietary_restrictions else None
        
        meal_plan = diet_advisor.generate_meal_plan(
            condition=condition,
            days=days,
            dietary_restrictions=restrictions_list
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "meal_plan": meal_plan
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "generate-meal-plan"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

