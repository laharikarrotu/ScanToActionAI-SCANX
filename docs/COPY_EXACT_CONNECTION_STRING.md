# ⚠️ CRITICAL: Copy Exact Connection String

## The Problem
"Tenant or user not found" means the connection string format is **slightly wrong**.

## Solution: Copy EXACTLY from Supabase Dashboard

### Step-by-Step:

1. **Go to Supabase Dashboard**
   - https://supabase.com/dashboard
   - Select project: `yphayjbfwxppmvxblbtr`

2. **Navigate to Database Settings**
   - Click **Settings** (gear icon) → **Database**
   - Scroll down to **"Connection string"** section

3. **Copy the Connection String**
   - You'll see 3 tabs: **URI**, **Transaction**, **Session**
   - Click **"Transaction"** tab (for connection pooler)
   - You'll see something like:
     ```
     postgresql://postgres.yphayjbfwxppmvxblbtr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
     ```
   - **COPY THE ENTIRE STRING** (including the brackets)

4. **Replace Password**
   - Replace `[YOUR-PASSWORD]` with: `gOy1z9O9ZlQm4qYK`
   - **DO NOT** URL-encode it (no special characters to encode)

5. **Update .env File**
   ```bash
   cd backend
   # Remove old line
   grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env
   # Add new line (paste your copied string here)
   echo "DATABASE_URL=postgresql://postgres.yphayjbfwxppmvxblbtr:gOy1z9O9ZlQm4qYK@aws-0-us-east-1.pooler.supabase.com:6543/postgres" >> .env
   ```

6. **Test**
   ```bash
   python3 test_database.py
   ```

## Why This Matters

The connection string format might have subtle differences:
- Username format might be different
- Host format might be different  
- Port might be different
- Database name might be different

**Copying directly from Supabase ensures 100% accuracy.**

## Current Status

✅ Database exists and is accessible (via MCP)
✅ Tables are created (4 tables)
❌ Backend connection string format is wrong

Once you copy the exact string, everything will work!

