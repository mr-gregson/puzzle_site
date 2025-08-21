#!/bin/bash

# Production startup script for Puzzle Site
# Make sure to set executable permissions: chmod +x start_production.sh

set -e

echo "🚀 Starting Puzzle Site in Production Mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Validate required environment variables
required_vars=("SECRET_KEY" "DATABASE_URL" "FLASK_ENV")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Setting up database..."
python migrations.py

# Create logs directory
mkdir -p logs

# Start the application with Gunicorn
echo "🌐 Starting Gunicorn server..."
echo "📍 Application will be available at http://0.0.0.0:${PORT:-8000}"

gunicorn --config gunicorn.conf.py wsgi:app