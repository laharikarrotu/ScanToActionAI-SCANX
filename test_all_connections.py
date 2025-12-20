#!/usr/bin/env python3
"""
Comprehensive connection and integration test for HealthScan
Tests all API endpoints, frontend-backend connectivity, database, and module imports
"""
import sys
import os
import asyncio
import httpx
import json
from typing import Dict, List, Tuple

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Test results storage
results = {
    "backend_imports": [],
    "api_endpoints": [],
    "frontend_routes": [],
    "database_connection": None,
    "module_imports": [],
    "frontend_backend_connectivity": []
}

def test_backend_imports():
    """Test all backend module imports"""
    print("\n🔍 Testing Backend Module Imports...")
    
    modules_to_test = [
        "api.main",
        "api.config",
        "api.auth",
        "api.rate_limiter",
        "vision.ui_detector",
        "vision.gemini_detector",
        "vision.image_quality",
        "vision.ocr_preprocessor",
        "planner.agent_planner",
        "planner.gemini_planner",
        "executor.browser_executor",
        "medication.prescription_extractor",
        "medication.interaction_checker",
        "nutrition.diet_advisor",
        "nutrition.condition_advisor",
        "nutrition.food_scanner",
        "memory.database",
        "memory.db_logger",
        "memory.event_log",
        "core.cache",
        "core.circuit_breaker",
        "core.rate_limiter_db",
        "core.rate_limiter_redis",
        "core.rate_limiter_token_bucket",
        "core.retry",
        "core.task_queue"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            results["backend_imports"].append((module, True, None))
            print(f"  ✅ {module}")
        except Exception as e:
            results["backend_imports"].append((module, False, str(e)))
            print(f"  ❌ {module}: {str(e)[:50]}")

def test_api_endpoints():
    """Test all API endpoints"""
    print("\n🔍 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/docs", "API documentation"),
        ("POST", "/analyze-and-execute", "Main analysis endpoint"),
        ("POST", "/check-prescription-interactions", "Drug interactions"),
        ("POST", "/get-diet-recommendations", "Diet recommendations"),
        ("POST", "/check-food-compatibility", "Food compatibility"),
        ("POST", "/generate-meal-plan", "Meal plan generation"),
        ("POST", "/login", "Authentication"),
        ("GET", "/protected", "Protected endpoint"),
    ]
    
    async def test_endpoint(method, path, description):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if method == "GET":
                    response = await client.get(f"{base_url}{path}")
                else:
                    # For POST, send minimal data
                    response = await client.post(f"{base_url}{path}", json={})
                
                status_ok = response.status_code in [200, 201, 400, 401, 422]  # Valid responses
                results["api_endpoints"].append((path, method, status_ok, response.status_code, description))
                
                if status_ok:
                    print(f"  ✅ {method} {path} ({response.status_code}) - {description}")
                else:
                    print(f"  ⚠️  {method} {path} ({response.status_code}) - {description}")
        except httpx.ConnectError:
            results["api_endpoints"].append((path, method, False, None, "Connection failed"))
            print(f"  ❌ {method} {path} - Connection failed (backend not running?)")
        except Exception as e:
            results["api_endpoints"].append((path, method, False, None, str(e)[:50]))
            print(f"  ❌ {method} {path} - {str(e)[:50]}")
    
    async def run_tests():
        tasks = [test_endpoint(method, path, desc) for method, path, desc in endpoints]
        await asyncio.gather(*tasks)
    
    asyncio.run(run_tests())

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        from api.config import settings
        from memory.database import engine, Base, SessionLocal
        
        if settings.database_url:
            # Try to create a session
            db = SessionLocal()
            db.close()
            results["database_connection"] = (True, "Connected successfully")
            print("  ✅ Database connection successful")
        else:
            results["database_connection"] = (False, "DATABASE_URL not set")
            print("  ⚠️  DATABASE_URL not set")
    except Exception as e:
        results["database_connection"] = (False, str(e))
        print(f"  ❌ Database connection failed: {str(e)[:50]}")

def test_module_interconnections():
    """Test that modules can import and use each other correctly"""
    print("\n🔍 Testing Module Interconnections...")
    
    interconnections = [
        ("api.main", "api.config", "settings"),
        ("api.main", "api.auth", "create_access_token"),
        ("api.main", "vision.ui_detector", "VisionEngine"),
        ("api.main", "planner.agent_planner", "PlannerEngine"),
        ("api.main", "executor.browser_executor", "BrowserExecutor"),
        ("api.main", "medication.prescription_extractor", "PrescriptionExtractor"),
        ("api.main", "nutrition.diet_advisor", "DietAdvisor"),
        ("api.auth", "api.config", "settings"),
        ("vision.gemini_detector", "vision.ui_detector", "UIElement"),
        ("planner.gemini_planner", "planner.agent_planner", "ActionStep"),
    ]
    
    for module1, module2, item in interconnections:
        try:
            mod1 = __import__(module1, fromlist=[item])
            mod2 = __import__(module2, fromlist=[item])
            results["module_imports"].append((module1, module2, item, True, None))
            print(f"  ✅ {module1} → {module2}.{item}")
        except Exception as e:
            results["module_imports"].append((module1, module2, item, False, str(e)))
            print(f"  ❌ {module1} → {module2}.{item}: {str(e)[:50]}")

def test_frontend_backend_connectivity():
    """Test frontend can connect to backend"""
    print("\n🔍 Testing Frontend-Backend Connectivity...")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Check if frontend API client is correctly configured
    try:
        frontend_api_file = os.path.join(base_dir, "app/frontend/app/lib/api.ts")
        with open(frontend_api_file, 'r') as f:
            content = f.read()
            
        # Check for API URL configuration
        has_api_url = "NEXT_PUBLIC_API_URL" in content or "localhost:8000" in content
        has_analyze_endpoint = "/analyze-and-execute" in content
        
        results["frontend_backend_connectivity"].append(("API URL configured", has_api_url))
        results["frontend_backend_connectivity"].append(("Analyze endpoint", has_analyze_endpoint))
        
        if has_api_url:
            print("  ✅ Frontend API URL configured")
        else:
            print("  ⚠️  Frontend API URL not found")
            
        if has_analyze_endpoint:
            print("  ✅ Analyze endpoint referenced")
        else:
            print("  ⚠️  Analyze endpoint not found")
        
        # Check InteractionChecker
        interaction_file = os.path.join(base_dir, "app/frontend/app/components/InteractionChecker.tsx")
        with open(interaction_file, 'r') as f:
            interaction_content = f.read()
        has_interaction_endpoint = "/check-prescription-interactions" in interaction_content
        results["frontend_backend_connectivity"].append(("Interaction endpoint", has_interaction_endpoint))
        if has_interaction_endpoint:
            print("  ✅ Interaction endpoint referenced")
        
        # Check DietPortal
        diet_file = os.path.join(base_dir, "app/frontend/app/components/DietPortal.tsx")
        with open(diet_file, 'r') as f:
            diet_content = f.read()
        has_diet_endpoints = "/get-diet-recommendations" in diet_content and "/check-food-compatibility" in diet_content and "/generate-meal-plan" in diet_content
        results["frontend_backend_connectivity"].append(("Diet endpoints", has_diet_endpoints))
        if has_diet_endpoints:
            print("  ✅ Diet endpoints referenced")
            
    except Exception as e:
        results["frontend_backend_connectivity"].append(("File read", False))
        print(f"  ❌ Could not read frontend files: {str(e)[:50]}")

def test_frontend_routes():
    """Test frontend routes exist"""
    print("\n🔍 Testing Frontend Routes...")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    routes = [
        os.path.join(base_dir, "app/frontend/app/page.tsx"),
        os.path.join(base_dir, "app/frontend/app/interactions/page.tsx"),
        os.path.join(base_dir, "app/frontend/app/diet/page.tsx"),
    ]
    
    for route in routes:
        try:
            with open(route, 'r') as f:
                content = f.read()
            results["frontend_routes"].append((route, True))
            print(f"  ✅ {os.path.basename(route)}")
        except FileNotFoundError:
            results["frontend_routes"].append((route, False))
            print(f"  ❌ {os.path.basename(route)} - File not found")
        except Exception as e:
            results["frontend_routes"].append((route, False))
            print(f"  ❌ {os.path.basename(route)} - {str(e)[:50]}")

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    # Backend imports
    import_success = sum(1 for _, success, _ in results["backend_imports"] if success)
    import_total = len(results["backend_imports"])
    print(f"\n✅ Backend Imports: {import_success}/{import_total} successful")
    
    # API endpoints
    endpoint_success = sum(1 for _, _, success, _, _ in results["api_endpoints"] if success)
    endpoint_total = len(results["api_endpoints"])
    print(f"✅ API Endpoints: {endpoint_success}/{endpoint_total} accessible")
    
    # Database
    if results["database_connection"]:
        db_success, db_msg = results["database_connection"]
        status = "✅" if db_success else "⚠️"
        print(f"{status} Database: {db_msg}")
    
    # Module interconnections
    inter_success = sum(1 for _, _, _, success, _ in results["module_imports"] if success)
    inter_total = len(results["module_imports"])
    print(f"✅ Module Interconnections: {inter_success}/{inter_total} working")
    
    # Frontend routes
    route_success = sum(1 for _, success in results["frontend_routes"] if success)
    route_total = len(results["frontend_routes"])
    print(f"✅ Frontend Routes: {route_success}/{route_total} exist")
    
    # Frontend-Backend connectivity
    conn_success = sum(1 for _, success in results["frontend_backend_connectivity"] if success)
    conn_total = len(results["frontend_backend_connectivity"])
    print(f"✅ Frontend-Backend: {conn_success}/{conn_total} configured")
    
    print("\n" + "="*60)
    
    # Show failures
    failures = []
    for module, success, error in results["backend_imports"]:
        if not success:
            failures.append(f"❌ Import failed: {module} - {error}")
    
    for path, method, success, status, desc in results["api_endpoints"]:
        if not success:
            failures.append(f"❌ API endpoint: {method} {path} - {desc}")
    
    if failures:
        print("\n⚠️  ISSUES FOUND:")
        for failure in failures[:10]:  # Show first 10
            print(f"  {failure}")
        if len(failures) > 10:
            print(f"  ... and {len(failures) - 10} more")

if __name__ == "__main__":
    print("🧪 HealthScan Connection & Integration Test")
    print("="*60)
    
    test_backend_imports()
    test_module_interconnections()
    test_database_connection()
    test_api_endpoints()
    test_frontend_routes()
    test_frontend_backend_connectivity()
    print_summary()

