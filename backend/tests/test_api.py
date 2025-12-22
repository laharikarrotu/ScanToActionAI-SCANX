"""
Simple API test script
Run this to verify the backend is working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_root():
    """Test root endpoint"""
    print("\nTesting / endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def main():
    print("HealthScan API Test")
    print("=" * 50)
    
    try:
        health_ok = test_health()
        root_ok = test_root()
        
        if health_ok and root_ok:
            print("\n✅ All basic tests passed!")
            print("\nTo test full functionality:")
            print("1. Start frontend: cd app/frontend && npm run dev")
            print("2. Open http://localhost:3000")
            print("3. Upload an image and test the features")
        else:
            print("\n❌ Some tests failed")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend")
        print("Make sure backend is running: cd backend && uvicorn api.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

