#!/usr/bin/env python3
"""
Test database connection and operations
"""
from memory.database import engine, SessionLocal, ScanRequest, UISchema, ActionPlan, ExecutionResult
from sqlalchemy import inspect

print('🔍 Testing Database Connection...')
try:
    # Test connection
    with engine.connect() as conn:
        print('✅ Database connection successful')
    
    # Check tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    table_list = ', '.join(tables)
    print(f'✅ Found {len(tables)} tables: {table_list}')
    
    # Test insert/query
    db = SessionLocal()
    try:
        # Count existing records
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

