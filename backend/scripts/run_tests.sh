#!/bin/bash
# Comprehensive Test Suite for HealthScan
# Tests backend, frontend, and integration

set -e  # Exit on error

echo "🧪 HealthScan Test Suite"
echo "========================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED:${NC} $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED:${NC} $2"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Backend Module Imports
echo "📦 Test 1: Backend Module Imports"
cd backend
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from api.config import settings
    from api.dependencies import vision_engine, planner_engine, combined_analyzer
    from executor.browser_executor import BrowserExecutor
    from medication.prescription_extractor import PrescriptionExtractor
    from nutrition.diet_advisor import DietAdvisor
    print('✅ All critical modules imported successfully')
    sys.exit(0)
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" 2>&1
test_result $? "Backend Module Imports"
cd ..

# Test 2: Backend Full Flow Test
echo ""
echo "🔄 Test 2: Backend Full Flow (Browser Cleanup)"
cd backend
if python3 tests/test_full_flow.py 2>&1 | tail -5; then
    test_result 0 "Backend Full Flow"
else
    test_result 1 "Backend Full Flow"
fi
cd ..

# Test 3: Frontend Build Test
echo ""
echo "🏗️  Test 3: Frontend Build"
cd app/frontend
if npm run build > /dev/null 2>&1; then
    test_result 0 "Frontend Build"
else
    test_result 1 "Frontend Build"
fi
cd ../..

# Test 4: TypeScript Type Check
echo ""
echo "📝 Test 4: TypeScript Type Check"
cd app/frontend
if npx tsc --noEmit > /dev/null 2>&1; then
    test_result 0 "TypeScript Type Check"
else
    echo "⚠️  TypeScript errors found (check manually)"
    test_result 1 "TypeScript Type Check"
fi
cd ../..

# Test 5: API Endpoints (if server running)
echo ""
echo "🌐 Test 5: API Endpoints (requires running server)"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    cd backend
    python3 tests/test_api_endpoints.py 2>&1
    test_result $? "API Endpoints"
    cd ..
else
    echo "⚠️  Backend server not running - skipping API tests"
    echo "   Start with: cd backend && uvicorn api.main:app --reload"
fi

# Summary
echo ""
echo "========================"
echo "📊 TEST SUMMARY"
echo "========================"
echo -e "${GREEN}✅ Passed:${NC} $TESTS_PASSED"
echo -e "${RED}❌ Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review output above.${NC}"
    exit 1
fi

