#!/bin/bash

# Supabase Connection String Setup
# Replace [YOUR-PASSWORD] and [REGION] with your actual values

echo "Setting up Supabase connection..."
echo ""
echo "Your project reference: yphayjbfwxppmvxblbtr"
echo ""
echo "Connection string format:"
echo "postgresql://postgres.yphayjbfwxppmvxblbtr:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
echo ""
echo "To find your region:"
echo "1. Go to Settings → General in Supabase dashboard"
echo "2. Look for 'Region' field"
echo ""
echo "Common regions:"
echo "  - us-east-1 (N. Virginia)"
echo "  - us-west-1 (N. California)"
echo "  - eu-west-1 (Ireland)"
echo "  - ap-southeast-1 (Singapore)"
echo ""
read -p "Enter your database password: " PASSWORD
read -p "Enter your region (e.g., us-east-1): " REGION

CONNECTION_STRING="postgresql://postgres.yphayjbfwxppmvxblbtr:${PASSWORD}@aws-0-${REGION}.pooler.supabase.com:6543/postgres"

echo ""
echo "Connection string:"
echo "$CONNECTION_STRING"
echo ""
echo "Adding to .env file..."

# Append to .env (or create if doesn't exist)
if grep -q "DATABASE_URL" backend/.env 2>/dev/null; then
    # Update existing
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=${CONNECTION_STRING}|" backend/.env
else
    # Add new
    echo "DATABASE_URL=${CONNECTION_STRING}" >> backend/.env
fi

echo "✅ Added to backend/.env"
echo ""
echo "Next steps:"
echo "1. pip3 install psycopg2-binary"
echo "2. python3 init_db.py"

