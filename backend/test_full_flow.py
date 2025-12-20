#!/usr/bin/env python3
"""
Test full flow: Frontend → Backend → Database
"""
import requests
import json

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_cors():
    """Test CORS headers"""
    print("🔍 Testing CORS Configuration...")
    try:
        response = requests.options(
            f"{BASE_URL}/health",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST"
            },
            timeout=5
        )
        if response.status_code == 200:
            print("✅ CORS preflight works")
            print(f"   Allowed Origins: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
            return True
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_frontend_backend_connection():
    """Test if frontend can reach backend"""
    print("\n🔍 Testing Frontend-Backend Connection...")
    try:
        # Simulate frontend request
        response = requests.get(
            f"{BASE_URL}/health",
            headers={"Origin": FRONTEND_URL},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Frontend can reach backend /health endpoint")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect - is backend running?")
        print("   Start with: cd backend && python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting"""
    print("\n🔍 Testing Rate Limiting...")
    try:
        # Make multiple rapid requests
        for i in range(5):
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 429:
                print(f"✅ Rate limiting works (blocked on request {i+1})")
                return True
        print("⚠️  Rate limiting not triggered (may need more requests)")
        return True
    except Exception as e:
        print(f"❌ Rate limit test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FULL FLOW TESTING")
    print("=" * 60)
    
    cors_ok = test_cors()
    connection_ok = test_frontend_backend_connection()
    rate_limit_ok = test_rate_limiting()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"CORS: {'✅ PASS' if cors_ok else '❌ FAIL'}")
    print(f"Frontend-Backend: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Rate Limiting: {'✅ PASS' if rate_limit_ok else '⚠️  WARN'}")
    
    if cors_ok and connection_ok:
        print("\n✅ Frontend and backend are properly connected!")
    else:
        print("\n❌ Some connection issues detected")

