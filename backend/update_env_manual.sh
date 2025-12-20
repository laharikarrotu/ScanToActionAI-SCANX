#!/bin/bash
# Manual update script - use this if setup_supabase.sh has issues

PASSWORD="gOy1z9O9ZlQm4qYK"
REGION="us-east-1"

# Create connection string WITHOUT ?pgbouncer=true (not needed for psycopg2)
CONNECTION_STRING="postgresql://postgres.yphayjbfwxppmvxblbtr:${PASSWORD}@aws-0-${REGION}.pooler.supabase.com:6543/postgres"

# Update .env file
if grep -q "DATABASE_URL" .env 2>/dev/null; then
    # Remove old DATABASE_URL line
    grep -v "DATABASE_URL" .env > .env.tmp && mv .env.tmp .env
fi

# Add new DATABASE_URL
echo "DATABASE_URL=${CONNECTION_STRING}" >> .env

echo "✅ Updated .env with connection string"
echo "Connection string: ${CONNECTION_STRING}"
