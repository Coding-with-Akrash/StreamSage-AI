# 🚀 StreamSage AI Assistant Setup Guide

## ⚡ Quick Setup (3 Steps)

### Step 1: Get Your OpenAI API Key
1. Visit: https://platform.openai.com/api-keys
2. Sign up/Login to your OpenAI account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. 📋 **Copy the key** (it starts with `sk-...`)

### Step 2: Configure StreamSage
**Option A: Edit Configuration File (Recommended)**
```bash
# Edit the secrets file
code .streamlit/secrets.toml
```
Replace `your-openai-api-key-here` with your actual API key:
```toml
OPENAI_API_KEY = "sk-your-real-api-key-here"
```

**Option B: Use Environment Variable**
```bash
export OPENAI_API_KEY="sk-your-real-api-key-here"
```

### Step 3: Launch StreamSage
```bash
streamlit run streamly.py
```

## 🔧 Troubleshooting API Key Issues

### Common Error Messages

**❌ "Incorrect API key provided"**
- ✅ **Solution**: Make sure your API key starts with `sk-`
- ✅ **Check**: Copy the complete key from OpenAI (no extra spaces)
- ✅ **Verify**: Ensure your OpenAI account has credits

**❌ "No secrets found"**
- ✅ **Check**: File exists at `.streamlit/secrets.toml`
- ✅ **Verify**: API key is not the placeholder text
- ✅ **Restart**: Restart Streamlit after updating the key

**❌ "401 Unauthorized"**
- ✅ **Validate**: API key is active (not revoked)
- ✅ **Account**: Check OpenAI account has API access
- ✅ **Billing**: Ensure account has credits or valid payment method

### 🔍 Debug Steps

1. **Check your API key format**:
   ```bash
   # Should start with "sk-" and be 51 characters long
   echo "Your API key should look like: sk-1234567890abcdef..."
   ```

2. **Verify file contents**:
   ```bash
   # Check if file exists and has correct content
   cat .streamlit/secrets.toml
   ```

3. **Test API key validity**:
   - Visit: https://platform.openai.com/api-keys
   - Ensure your key is listed and active

## 📸 Screenshots

### API Key Setup
1. **OpenAI Dashboard**: Get your API key from here
2. **Configuration File**: Edit `.streamlit/secrets.toml`
3. **StreamSage Running**: Successfully connected interface

## 💡 Tips for Success

- 🔐 **Keep your API key secure** - never commit it to version control
- 💳 **Monitor your usage** - check OpenAI dashboard for billing
- 🔄 **Restart after changes** - Streamlit needs restart for config updates
- 📝 **Save your key** - store it securely in a password manager

## 🚨 Getting Help

If you continue having issues:
1. 📖 Check this setup guide again
2. 🐛 Review the troubleshooting section above
3. 🔗 Visit: https://github.com/Coding-with-Akrash/StreamSage/issues
4. 💬 Create a new issue with your error message

---

**🎉 Happy Streamlit Development with StreamSage!**

## Features

### 🎯 Main Modes
- **Latest Updates**: Browse Streamlit's latest features and changes
- **Chat with StreamSage**: Interactive AI assistant for Streamlit help

### 💡 Basic Interactions
- Ask questions about Streamlit features
- Get code examples and snippets
- Learn syntax and best practices
- Browse latest updates

### ⚡ Advanced Interactions
- Generate complete Streamlit apps
- Get detailed code explanations
- Receive project analysis & feedback
- Debug and fix coding issues

## Configuration

### Using Environment Variables (Alternative)
```bash
export OPENAI_API_KEY="your-api-key-here"
streamlit run streamly.py
```

### Custom Settings
You can add more configuration options to `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-api-key-here"
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
```

## Troubleshooting

### "No secrets found" Error
- Ensure `.streamlit/secrets.toml` exists in your project root
- Check that the file contains a valid `OPENAI_API_KEY`
- Make sure you're running from the correct directory

### API Key Issues
- Verify your API key is correct and active
- Check your OpenAI account has sufficient credits
- Ensure the key has the right permissions

## Support

- **GitHub**: https://github.com/Coding-with-Akrash/
- **Documentation**: Streamlit Docs - https://docs.streamlit.io

---

**Happy Streamlit Development with StreamSage!** 🎉