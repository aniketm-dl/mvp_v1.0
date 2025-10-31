# API Keys Setup Guide

This project requires API keys to run. Follow the steps below to configure your environment.

## Required API Keys

### 1. OpenAI API Key
The backend uses OpenAI GPT-4 for digital twin LLM responses.

**Get your key:**
- Sign up at [https://platform.openai.com/](https://platform.openai.com/)
- Navigate to API keys section
- Create a new secret key

**Set as environment variable:**
```bash
export OPENAI_API_KEY="sk-proj-..."
```

### 2. AWS Credentials (Optional)
Only required if using AWS services like S3 for data storage.

**Get your credentials:**
- Sign in to AWS Console
- Navigate to IAM > Users > Security Credentials
- Create access key

**Set as environment variables:**
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
```

## Configuration Files

### Method 1: Environment Variables (Recommended)
Set environment variables in your shell:

```bash
# Add to ~/.bashrc or ~/.zshrc for persistence
export OPENAI_API_KEY="sk-proj-..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### Method 2: Claude Code Settings (Local Development)
Create a local settings file:

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

Then edit `.claude/settings.local.json` and add your keys:
```json
{
  "permissions": {
    "allow": [],
    "deny": [],
    "ask": [],
    "defaultMode": "bypassPermissions"
  }
}
```

**Note:** The actual API keys should be set as environment variables, not stored in this file.

## Running the Application

### Backend
```bash
cd /path/to/mvp_v1.0
export PYTHONPATH="$PWD"
export OPENAI_API_KEY="your-key-here"
uvicorn src.api.service_airline:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd ui
npm install
npm run dev
```

## Security Best Practices

1. **Never commit API keys to git**
   - `.claude/settings.local.json` is already in `.gitignore`
   - Use environment variables instead

2. **Rotate keys regularly**
   - Especially if they may have been exposed

3. **Use restricted keys**
   - Create keys with minimum required permissions
   - For AWS, use IAM roles with specific policies

4. **Monitor usage**
   - Check OpenAI dashboard for API usage
   - Set up billing alerts

## Troubleshooting

### "Failed to send message" Error
- Ensure `OPENAI_API_KEY` is set correctly
- Check backend logs: `tail -f logs/service.log`
- Verify key is valid at [https://platform.openai.com/](https://platform.openai.com/)

### Backend won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Kill existing process: `kill -9 $(lsof -t -i:8000)`

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check API base URL in `ui/src/api/client.ts`

## Need Help?

If you encounter issues:
1. Check the main [README.md](README.md)
2. Review backend logs
3. Verify all environment variables are set
4. Ensure dependencies are installed
