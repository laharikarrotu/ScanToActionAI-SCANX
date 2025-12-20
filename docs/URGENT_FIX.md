# ⚠️ URGENT: Copy Connection String from Supabase Dashboard

## Current Status
- ✅ Connection string has correct format (region, password, pooler, port)
- ❌ Still getting "Tenant or user not found" error
- ✅ Database works via MCP (tables exist)

## The Problem
The connection string format we're using might be slightly different from what Supabase expects. The username format, password encoding, or other details might be wrong.

## SOLUTION: Copy EXACT String from Dashboard

### Steps:

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard
   - Select project: `yphayjbfwxppmvxblbtr`

2. **Get Connection String**
   - Click **Settings** → **Database**
   - Scroll to **"Connection string"** section
   - Click **"Transaction"** tab
   - You'll see a connection string like:
     ```
     postgresql://postgres.yphayjbfwxppmvxblbtr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
     ```

3. **Copy the ENTIRE string** (including brackets)

4. **Replace Password**
   - Replace `[YOUR-PASSWORD]` with: `gOy1z9O9ZlQm4qYK`
   - **DO NOT** add any URL encoding

5. **Update .env**
   ```bash
   cd backend
   # Remove old line
   grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env
   # Add new line (paste your EXACT copied string here)
   echo "DATABASE_URL=<paste-your-exact-string-here>" >> .env
   ```

6. **Test**
   ```bash
   python3 test_database.py
   ```

## Why This Is Necessary

The connection string format might have subtle differences:
- Username format might be different
- Password encoding might be different
- Host format might be different
- There might be additional parameters

**Copying directly from Supabase ensures 100% accuracy.**

## Alternative: Use Direct Connection (if pooler doesn't work)

If the pooler still doesn't work, you can try the direct connection format (but this requires IPv6 or paid plan):

```
postgresql://postgres:[PASSWORD]@db.yphayjbfwxppmvxblbtr.supabase.co:5432/postgres
```

But for free plan, pooler should work - you just need the EXACT format from Supabase.

