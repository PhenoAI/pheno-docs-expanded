#!/bin/bash

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║         🚀 DEPLOYING PHENO DOCS WITH CHATBOT 🚀            ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create a .env file with your BACKEND_URL"
    echo ""
    echo "Example:"
    echo "BACKEND_URL=https://your-backend.railway.app/api/chat"
    echo ""
    echo "For local development, use:"
    echo "BACKEND_URL=http://localhost:5000/api/chat"
    exit 1
fi

# Load backend URL from .env
source .env

if [ -z "$BACKEND_URL" ]; then
    echo "❌ ERROR: BACKEND_URL not found in .env file!"
    echo ""
    echo "Please add BACKEND_URL to your .env file:"
    echo "BACKEND_URL=https://your-backend-url.com/api/chat"
    exit 1
fi

echo "✅ Step 1: Backend URL loaded from .env"
echo "   Backend URL: $BACKEND_URL"
echo ""

# Create knowledge base context
echo "📚 Step 2: Creating knowledge base context..."
./create-knowledge-base.sh
echo ""

# Inject backend URL into widget
echo "🔗 Step 3: Injecting backend URL into chatbot widget..."
WIDGET_FILE="pheno_knowledge_base_expanded/chatbot-widget-simple.html"
WIDGET_TEMP="pheno_knowledge_base_expanded/.chatbot-widget-temp.html"

# Replace placeholder with actual backend URL
sed "s|__BACKEND_URL__|$BACKEND_URL|g" "$WIDGET_FILE" > "$WIDGET_TEMP"
mv "$WIDGET_TEMP" "$WIDGET_FILE"

echo "✅ Backend URL injected successfully"
echo ""

# Build the site
echo "🏗️  Step 4: Building Quarto site..."
cd pheno_knowledge_base_expanded
quarto render
cd ..
echo ""

# Restore placeholder in widget (so we don't commit the URL)
echo "🔒 Step 5: Restoring placeholder in widget..."
sed "s|$BACKEND_URL|__BACKEND_URL__|g" "$WIDGET_FILE" > "$WIDGET_TEMP"
mv "$WIDGET_TEMP" "$WIDGET_FILE"

echo "✅ Placeholder restored (backend URL not in source)"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║                  ✅ DEPLOYMENT COMPLETE! ✅                 ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Output: docs/"
echo "🌐 Your site is ready with the chatbot (backend URL included)"
echo "🔒 Source code still has placeholder (safe to commit)"
echo ""
echo "⚠️  IMPORTANT: Make sure your backend is running and accessible!"
echo ""
echo "Next steps:"
echo "  1. Ensure backend is running at: $BACKEND_URL"
echo "  2. Test locally: cd docs && python3 -m http.server 8000"
echo "  3. Deploy docs/ to GitHub Pages"
echo ""








