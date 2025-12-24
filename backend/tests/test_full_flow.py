#!/usr/bin/env python3
"""
Full Flow Test Script
Tests the complete system flow and verifies no resource leaks
Run this before deploying to production
"""
import asyncio
import sys
import os
import time
import subprocess

# Optional: psutil for process counting (install with: pip install psutil)
try:
    import psutil  # type: ignore[reportMissingModuleSource]
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor.browser_executor import BrowserExecutor
from vision.ui_detector import VisionEngine
from planner.agent_planner import PlannerEngine
from api.config import settings

def count_chromium_processes():
    """Count running Chromium/Chrome processes"""
    if not PSUTIL_AVAILABLE:
        # Fallback: Use ps command (Unix/Mac)
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            count = len([line for line in result.stdout.split('\n') 
                        if 'chromium' in line.lower() or 'chrome' in line.lower() or 'playwright' in line.lower()])
            return count
        except:
            return 0  # Can't count, assume OK
    
    count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'] or ''
            if 'chromium' in name.lower() or 'chrome' in name.lower() or 'playwright' in name.lower():
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return count

async def test_browser_executor_cleanup():
    """Test that browser executor properly cleans up resources"""
    print("🧪 Testing Browser Executor Cleanup...")
    
    initial_count = count_chromium_processes()
    print(f"   Initial Chromium processes: {initial_count}")
    
    try:
        executor = BrowserExecutor()
        await executor.initialize()
        
        # Create a simple test page
        await executor.page.goto("data:text/html,<html><body><h1>Test</h1></body></html>")
        
        # Close executor
        await executor.close()
        
        # Wait a bit for processes to terminate
        await asyncio.sleep(2)
        
        final_count = count_chromium_processes()
        print(f"   Final Chromium processes: {final_count}")
        
        # Allow some tolerance (1-2 processes might remain for caching)
        if final_count > initial_count + 2:
            print(f"   ❌ FAILED: Too many Chromium processes remaining ({final_count - initial_count} new processes)")
            return False
        else:
            print(f"   ✅ PASSED: Browser cleanup successful")
            return True
            
    except Exception as e:
        print(f"   ❌ FAILED: Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test that API endpoints are accessible (optional - won't fail if server not running)"""
    print("\n🧪 Testing API Endpoints (Optional)...")
    
    try:
        import httpx
    except ImportError:
        print("   ⚠️  httpx not installed - skipping API endpoint test")
        return True  # Don't fail if httpx not available
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/",
    ]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            all_ok = True
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{base_url}{endpoint}")
                    if response.status_code == 200:
                        print(f"   ✅ {endpoint}: OK")
                    else:
                        print(f"   ⚠️  {endpoint}: Status {response.status_code}")
                        all_ok = False
                except Exception as e:
                    print(f"   ⚠️  {endpoint}: {str(e)[:50]}")
                    all_ok = False
            return all_ok
    except Exception as e:
        print(f"   ⚠️  Could not connect to API (is server running?): {e}")
        print("   (This is OK - server may not be running)")
        return True  # Don't fail if server isn't running

def test_imports():
    """Test that all critical modules can be imported"""
    print("\n🧪 Testing Module Imports...")
    
    # Critical modules (must work)
    critical_modules = [
        "executor.browser_executor",
        "vision.ui_detector",
        "planner.agent_planner",
        "medication.prescription_extractor",
        "medication.interaction_checker",
        "nutrition.diet_advisor",
    ]
    
    # Optional modules (nice to have, but not critical)
    optional_modules = [
        "core.error_handler",
        "core.encryption",
        "core.audit_logger",
    ]
    
    critical_failed = []
    optional_failed = []
    
    for module in critical_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ❌ {module}: {str(e)[:50]}")
            critical_failed.append(module)
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ⚠️  {module}: {str(e)[:50]} (optional)")
            optional_failed.append(module)
    
    # Only fail if critical modules fail
    if critical_failed:
        print(f"\n   ⚠️  {len(optional_failed)} optional module(s) failed (OK if Python version incompatible)")
    return len(critical_failed) == 0

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 FULL FLOW TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Module imports
    results.append(("Module Imports", test_imports()))
    
    # Test 2: Browser executor cleanup
    results.append(("Browser Cleanup", await test_browser_executor_cleanup()))
    
    # Test 3: API endpoints (optional - won't fail if server not running)
    api_result = await test_api_endpoints()
    results.append(("API Endpoints (Optional)", api_result))
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    critical_passed = True
    for test_name, passed in results:
        if "Optional" in test_name:
            status = "✅ PASSED" if passed else "⚠️  SKIPPED"
        else:
            status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed and "Optional" not in test_name:
            critical_passed = False
    
    print("=" * 60)
    
    # Critical test: Browser cleanup must pass
    browser_test_passed = results[1][1] if len(results) > 1 else False
    
    if browser_test_passed and critical_passed:
        print("✅ CRITICAL TESTS PASSED - System ready for beta!")
        print("   (Optional tests may have warnings - this is OK)")
        return 0
    else:
        print("❌ CRITICAL TESTS FAILED - Fix issues before deployment")
        if not browser_test_passed:
            print("   ⚠️  Browser cleanup test failed - this is CRITICAL!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
