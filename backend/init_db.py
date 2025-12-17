"""
Initialize database tables
Run this once after setting up Supabase connection
"""
from memory.database import init_db

if __name__ == "__main__":
    print("Initializing database tables...")
    init_db()
    print("✅ Database tables created successfully!")

