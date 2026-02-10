#!/bin/bash

set -e

echo "📦 Packaging Lambda function..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "📁 Working directory: $TEMP_DIR"

# Copy Lambda function
echo "📋 Copying Lambda function..."
cp lambda_function.py "$TEMP_DIR/"

# Copy context file
echo "📚 Copying knowledge base context..."
if [ -f "../pheno_knowledge_base_expanded/knowledge-base-context.txt" ]; then
    cp "../pheno_knowledge_base_expanded/knowledge-base-context.txt" "$TEMP_DIR/"
    echo "✅ Context file copied"
else
    echo "⚠️  Warning: Context file not found. Run ../create-knowledge-base.sh first"
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip3 install -r requirements.txt -t "$TEMP_DIR/" --quiet

# Create zip file
echo "🗜️  Creating deployment package..."
cd "$TEMP_DIR"
zip -r ../lambda-deployment.zip . -q
cd - > /dev/null

# Move zip to lambda directory
mv "$TEMP_DIR/../lambda-deployment.zip" ./lambda-deployment.zip

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Lambda package created: lambda-deployment.zip"
echo "📊 Package size: $(du -h lambda-deployment.zip | cut -f1)"
