#!/bin/bash
# Fix .env file with correct connection string

# Remove ALL DATABASE_URL lines
grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env

# Add correct connection string with region
echo "DATABASE_URL=postgresql://postgres.yphayjbfwxppmvxblbtr:gOy1z9O9ZlQm4qYK@aws-0-us-east-1.pooler.supabase.com:6543/postgres" >> .env

echo "✅ Fixed .env file"
echo ""
echo "Current DATABASE_URL:"
grep DATABASE_URL .env
