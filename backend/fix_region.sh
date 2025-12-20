#!/bin/bash
# Fix connection string with CORRECT region: us-west-2

# Remove old DATABASE_URL
grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env

# Add correct connection string with us-west-2 region
echo "DATABASE_URL=postgresql://postgres.yphayjbfwxppmvxblbtr:gOy1z9O9ZlQm4qYK@aws-0-us-west-2.pooler.supabase.com:6543/postgres" >> .env

echo "✅ Fixed connection string with CORRECT region: us-west-2"
echo ""
echo "Current DATABASE_URL:"
grep DATABASE_URL .env
