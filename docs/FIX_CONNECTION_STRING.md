# Fix Supabase Connection String (Free Plan)

## Issue
You're on the **Free Plan**, which means:
- ✅ **Connection Pooler works** (port 6543) - This is what you should use!
- ❌ Direct IPv4 connections require paid plan ($4/month)
- ✅ IPv6 direct connections work, but pooler is easier

## Solution: Use Connection Pooler

The pooler connection string format should be:

```
postgresql://postgres.yphayjbfwxppmvxblbtr:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pgbouncer=true
```

## Steps to Fix

### 1. Get Your Region
1. Go to Supabase Dashboard → **Settings → General**
2. Find **"Region"** field (e.g., `us-east-1`, `us-west-1`, `eu-west-1`)

### 2. Get Connection String from Dashboard
1. Go to **Settings → Database**
2. Scroll to **"Connection string"** section
3. Click **"Transaction"** or **"Session"** tab (NOT "URI")
4. Copy the connection string
5. It should look like:
   ```
   postgresql://postgres.yphayjbfwxppmvxblbtr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

### 3. Update backend/.env

Replace `[YOUR-PASSWORD]` with your actual password (URL-encode special characters):
- `@` → `%40`
- `!` → `%21`
- `#` → `%23`
- `$` → `%24`

Example: Password `Lahari@123!` becomes `Lahari%40123%21`

### 4. Add `?pgbouncer=true` Parameter

Add this parameter to enable connection pooling:
```
postgresql://postgres.yphayjbfwxppmvxblbtr:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pgbouncer=true
```

## Why Pooler Works on Free Plan

- ✅ Pooler resolves to IPv4 addresses automatically
- ✅ No need for dedicated IPv4 add-on
- ✅ Works with all clients
- ✅ Better for connection management

## Verify Connection

After updating `.env`, test:
```bash
cd backend
python3 test_database.py
```

If it works, you'll see:
```
✅ Database connection successful
✅ Found 4 tables: ...
```

