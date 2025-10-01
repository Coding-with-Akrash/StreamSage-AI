#!/bin/bash

# 🚀 StreamSage Quick Setup Script
# This script helps you configure your OpenAI API key for StreamSage

echo "🚀 StreamSage AI Assistant - Quick Setup"
echo "========================================"

# Check if .streamlit directory exists
if [ ! -d ".streamlit" ]; then
    echo "📁 Creating .streamlit directory..."
    mkdir -p .streamlit
fi

# Check if secrets.toml exists
if [ -f ".streamlit/secrets.toml" ]; then
    echo "📄 Found existing secrets.toml file"
    read -p "🔄 Do you want to update your API key? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Using existing configuration"
        exit 0
    fi
else
    echo "📄 Creating new secrets.toml file..."
fi

echo
echo "🔑 Please enter your OpenAI API key:"
echo "   Get it from: https://platform.openai.com/api-keys"
echo "   Format: sk-... (starts with 'sk-')"
echo

read -s api_key

# Validate API key format
if [[ ! $api_key =~ ^sk- ]]; then
    echo
    echo "❌ Error: API key must start with 'sk-'"
    echo "   Please make sure you copied the complete key from OpenAI"
    exit 1
fi

# Create or update secrets.toml
cat > .streamlit/secrets.toml << EOF
# 🚀 StreamSage Configuration
# Generated on: $(date)

# 🔑 OpenAI API Key
OPENAI_API_KEY = "$api_key"

# ⚙️ Optional Configuration
# MODEL_NAME = "gpt-4o-mini"
# MAX_TOKENS = 2000
# TEMPERATURE = 0.7
EOF

echo
echo "✅ API key configured successfully!"
echo "📁 File saved to: .streamlit/secrets.toml"
echo
echo "🚀 Next steps:"
echo "   1. Run: streamlit run streamly.py"
echo "   2. Enjoy your StreamSage AI assistant!"
echo
echo "💡 Tip: Keep your API key secure and don't share it publicly"