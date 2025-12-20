# Verify Supabase Connection

## If Supabase is connected to Cursor (via MCP):

Great! But you still need to update `backend/.env` with the correct connection string.

## Steps to Fix:

### 1. Get Connection String from Supabase Dashboard

1. Go to **Settings → Database** in Supabase
2. Scroll to **"Connection string"**
3. Click **"URI"** tab (NOT Transaction or Session)
4. Copy the connection string

It should look like:
```
postgresql://postgres:[YOUR-PASSWORD]@db.yphayjbfwxppmvxblbtr.supabase.co:5432/postgres
```

### 2. Update backend/.env

Open `backend/.env` and update:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.yphayjbfwxppmvxblbtr.supabase.co:5432/postgres
```

**Important**: 
- Replace `[YOUR-PASSWORD]` with your actual password
- If password has special characters, URL-encode them:
  - `@` → `%40`
  - `!` → `%21`
  - `#` → `%23`
  - `$` → `%24`

### 3. Test Connection

```bash
cd backend
python3 init_db.py
```

This should create 4 tables:
- `scan_requests`
- `ui_schemas`
- `action_plans`
- `execution_results`

### 4. Verify in Supabase Dashboard

Go to **Database → Tables** in Supabase dashboard. You should see all 4 tables.

## Common Issues:

- **"Tenant or user not found"**: Wrong connection string format or wrong password
- **"Connection refused"**: Wrong host/port
- **"SSL required"**: Use the connection string from Supabase dashboard (it includes SSL)

## Quick Fix Script:

You can also use the updated `setup_supabase.sh`:
```bash
cd backend
bash setup_supabase.sh
```

