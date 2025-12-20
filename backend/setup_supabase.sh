#!/bin/bash

# Supabase Connection String Setup
# Replace [YOUR-PASSWORD] and [REGION] with your actual values

echo "Setting up Supabase connection..."
echo ""
echo "Your project reference: yphayjbfwxppmvxblbtr"
echo ""
echo "For FREE PLAN: Use Connection Pooler (port 6543)"
echo ""
echo "1. Go to Supabase Dashboard → Settings → Database"
echo "2. Scroll to 'Connection string' section"
echo "3. Click 'Transaction' or 'Session' tab (NOT 'URI')"
echo "4. Copy the connection string"
echo ""
echo "OR enter manually:"
echo ""
read -p "Enter your database password: " PASSWORD
read -p "Enter your region (e.g., us-east-1): " REGION

# URL encode common special characters in password
ENCODED_PASSWORD=$(echo "$PASSWORD" | sed 's/@/%40/g; s/#/%23/g; s/\$/%24/g; s/%/%25/g; s/&/%26/g; s/+/%2B/g; s/=/%3D/g; s/!/%21/g')

# Use connection pooler (port 6543) - works on free plan!
# Note: Don't add ?pgbouncer=true - psycopg2 doesn't support it
CONNECTION_STRING="postgresql://postgres.yphayjbfwxppmvxblbtr:${ENCODED_PASSWORD}@aws-0-${REGION}.pooler.supabase.com:6543/postgres"

echo ""
echo "Connection string:"
echo "$CONNECTION_STRING"
echo ""
echo "Adding to .env file..."

# Append to .env (or create if doesn't exist)
# Script runs from backend/ directory, so use .env (not backend/.env)
if grep -q "DATABASE_URL" .env 2>/dev/null; then
    # Update existing - escape special characters for sed
    ESCAPED_STRING=$(echo "$CONNECTION_STRING" | sed 's/[[\.*^$()+?{|]/\\&/g')
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=${ESCAPED_STRING}|" .env
else
    # Add new
    echo "DATABASE_URL=${CONNECTION_STRING}" >> .env
fi

echo "✅ Added to .env"
echo ""
echo "Next steps:"
echo "1. pip3 install psycopg2-binary"
echo "2. python3 init_db.py"

