#!/bin/bash
# Fix connection string with correct region

PASSWORD="gOy1z9O9ZlQm4qYK"
REGION="us-east-1"

# Remove old DATABASE_URL
grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env

# Add correct connection string with region
CONNECTION_STRING="postgresql://postgres.yphayjbfwxppmvxblbtr:${PASSWORD}@aws-0-${REGION}.pooler.supabase.com:6543/postgres"

echo "DATABASE_URL=${CONNECTION_STRING}" >> .env

echo "✅ Fixed connection string"
echo "Connection string: ${CONNECTION_STRING}"
