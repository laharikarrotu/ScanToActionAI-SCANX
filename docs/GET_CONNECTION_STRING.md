# Get Correct Connection String from Supabase

## The Issue
"Tenant or user not found" means the connection string format is wrong.

## Solution: Copy from Dashboard

### Step 1: Go to Supabase Dashboard
1. Open https://supabase.com/dashboard
2. Select your project: `yphayjbfwxppmvxblbtr`

### Step 2: Get Connection String
1. Click **Settings** (gear icon) → **Database**
2. Scroll to **"Connection string"** section
3. You'll see 3 tabs: **URI**, **Transaction**, **Session**

### Step 3: Copy the Correct One
For **Connection Pooler** (free plan), use **"Transaction"** or **"Session"** tab:

**Transaction mode** (recommended):
```
postgresql://postgres.yphayjbfwxppmvxblbtr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Session mode**:
```
postgresql://postgres.yphayjbfwxppmvxblbtr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 4: Update .env
1. Copy the ENTIRE connection string from Supabase
2. Replace `[YOUR-PASSWORD]` with your actual password: `gOy1z9O9ZlQm4qYK`
3. The final string should be:
   ```
   postgresql://postgres.yphayjbfwxppmvxblbtr:gOy1z9O9ZlQm4qYK@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
4. Update `backend/.env`:
   ```bash
   cd backend
   # Remove old DATABASE_URL line
   grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env
   # Add new one
   echo "DATABASE_URL=postgresql://postgres.yphayjbfwxppmvxblbtr:gOy1z9O9ZlQm4qYK@aws-0-us-east-1.pooler.supabase.com:6543/postgres" >> .env
   ```

### Step 5: Test
```bash
cd backend
python3 test_database.py
```

## Important Notes

- **Don't add** `?pgbouncer=true` - psycopg2 doesn't support it
- **Use Transaction mode** for most cases
- **Password**: `gOy1z9O9ZlQm4qYK` (no special characters to encode)
- **Region**: `us-east-1` (verify in Settings → General)

## If Still Not Working

The connection string format might be slightly different. Copy it **exactly** as shown in Supabase Dashboard, including:
- Exact username format
- Exact host format  
- Exact port number
- Exact database name

