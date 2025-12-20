# Fix Database Connection Issue

## Error: "Tenant or user not found"

This means your Supabase connection string is incorrect.

## How to Get Correct Connection String

### Option 1: From Supabase Dashboard (Easiest)

1. Go to **Settings → Database** in Supabase
2. Scroll to **Connection string**
3. Select **"URI"** tab (not Transaction or Session)
4. Copy the connection string
5. It should look like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.yphayjbfwxppmvxblbtr.supabase.co:5432/postgres
   ```

### Option 2: Direct Connection (Recommended)

Use the **direct connection** (port 5432) instead of pooler (port 6543):

```
postgresql://postgres:[PASSWORD]@db.yphayjbfwxppmvxblbtr.supabase.co:5432/postgres
```

**NOT** the pooler:
```
postgresql://postgres.yphayjbfwxppmvxblbtr:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

### Option 3: Update .env Manually

1. Get connection string from Supabase dashboard
2. URL-encode the password (if it has special characters)
3. Update `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.yphayjbfwxppmvxblbtr.supabase.co:5432/postgres
   ```

### Password URL Encoding

If password has special characters, encode them:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`
- `+` → `%2B`
- `=` → `%3D`

Example: Password `Lahari@123!` becomes `Lahari%40123%21`

## After Fixing Connection String

Run:
```bash
cd backend
python3 init_db.py
```

This will create all tables in Supabase.

