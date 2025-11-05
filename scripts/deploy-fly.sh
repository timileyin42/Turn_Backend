#!/bin/bash
# Quick deployment script for Fly.io

set -e  # Exit on error

echo "🚀 Starting deployment to Fly.io..."

# Check if flyctl is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI is not installed. Install it from: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if user is logged in
if ! fly auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Run: fly auth login"
    exit 1
fi

# Check if fly.toml exists
if [ ! -f "fly.toml" ]; then
    echo "❌ fly.toml not found. Run: fly launch"
    exit 1
fi

# Deploy
echo "📦 Building and deploying..."
fly deploy --dockerfile Dockerfile.fly

# Check status
echo "✅ Deployment complete! Checking status..."
fly status

echo ""
echo "🎉 Deployment successful!"
echo "📝 View logs: fly logs"
echo "🌐 Open app: fly open"
echo "📊 Dashboard: fly dashboard"
