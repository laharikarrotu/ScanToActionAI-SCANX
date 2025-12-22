#!/bin/bash
# Start both servers for testing

echo "🚀 Starting HealthScan for Testing"
echo "=================================="
echo ""

# Check if ports are available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 already in use (backend may be running)"
else
    echo "✅ Port 8000 available"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 3000 already in use (frontend may be running)"
else
    echo "✅ Port 3000 available"
fi

echo ""
echo "📋 To start servers:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  uvicorn api.main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd app/frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "🧪 Test Checklist:"
echo "  □ Upload prescription image"
echo "  □ Check drug interactions"
echo "  □ Get diet recommendations"
echo "  □ Test form automation"
echo ""

