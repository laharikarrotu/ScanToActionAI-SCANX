#!/bin/bash
# Quick Test Script - Tests what we can without full environment

echo "🧪 Quick HealthScan Tests"
echo "========================"
echo ""

# Test 1: Frontend TypeScript
echo "📝 Test 1: Frontend TypeScript"
cd app/frontend
if npx tsc --noEmit 2>&1 | grep -q "error"; then
    echo "❌ TypeScript errors found"
    npx tsc --noEmit 2>&1 | head -10
else
    echo "✅ TypeScript: OK"
fi
cd ../..

# Test 2: Frontend Structure
echo ""
echo "📁 Test 2: Frontend Structure"
if [ -f "app/frontend/app/lib/api.ts" ] && [ -f "app/frontend/app/components/ScanPage.tsx" ]; then
    echo "✅ Frontend files: OK"
else
    echo "❌ Missing frontend files"
fi

# Test 3: Backend Structure
echo ""
echo "📁 Test 3: Backend Structure"
if [ -f "backend/api/main.py" ] && [ -f "backend/api/dependencies.py" ]; then
    echo "✅ Backend files: OK"
else
    echo "❌ Missing backend files"
fi

# Test 4: API Routes
echo ""
echo "🔌 Test 4: API Routes Check"
cd backend
if grep -q "@router.post" api/routers/prescription.py && \
   grep -q "@router.post" api/routers/medication.py && \
   grep -q "@router.post" api/routers/nutrition.py; then
    echo "✅ API routes: OK"
else
    echo "❌ Missing API routes"
fi
cd ..

# Test 5: Environment Check
echo ""
echo "🔐 Test 5: Environment Variables"
if [ -f "backend/.env" ] || [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "⚠️  .env file not found (create one for production)"
fi

echo ""
echo "========================"
echo "✅ Quick tests complete!"
echo ""
echo "Next: Start servers and test manually:"
echo "  Backend:  cd backend && uvicorn api.main:app --reload"
echo "  Frontend: cd app/frontend && npm run dev"

