#!/usr/bin/env python3
"""Quick connection test"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
url = os.getenv('DATABASE_URL', '')

print(f"Testing connection string: {url[:50]}...")
print()

try:
    conn = psycopg2.connect(url)
    print("✅ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ PostgreSQL version: {version[0][:50]}...")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
