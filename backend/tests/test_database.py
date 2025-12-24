#!/usr/bin/env python3
"""
Test database connection and operations
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.database import engine, SessionLocal, ScanRequest, UISchema, ActionPlan, ExecutionResult, init_db
from sqlalchemy import inspect

print('🔍 Testing Database Connection...')
try:
    # Test connection
    with engine.connect() as conn:
        print('✅ Database connection successful')
    
    # Initialize tables if they don't exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['scan_requests', 'ui_schemas', 'action_plans', 'execution_results']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(f'⚠️  Missing tables: {missing_tables}')
        print('📦 Creating database tables...')
        init_db()
        # Re-check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f'✅ Found {len(tables)} tables after initialization')
    else:
        table_list = ', '.join(tables)
        print(f'✅ Found {len(tables)} tables: {table_list}')
    
    # Test insert/query
    db = SessionLocal()
    try:
        # Count existing records (should work now that tables exist)
        scan_count = db.query(ScanRequest).count()
        print(f'✅ Can query scan_requests: {scan_count} records')
        
        ui_count = db.query(UISchema).count()
        print(f'✅ Can query ui_schemas: {ui_count} records')
        
        plan_count = db.query(ActionPlan).count()
        print(f'✅ Can query action_plans: {plan_count} records')
        
        result_count = db.query(ExecutionResult).count()
        print(f'✅ Can query execution_results: {result_count} records')
        
        print('✅ All database operations working!')
    finally:
        db.close()
        
except Exception as e:
    print(f'❌ Database error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

