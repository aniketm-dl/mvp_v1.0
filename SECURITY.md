# Security Policy and Best Practices

## 🔒 Overview

This document outlines the security practices for managing API keys, credentials, and sensitive data in the Darpan Labs MVP project.

## 🚨 CRITICAL: Never Commit Secrets to Git

**UNDER NO CIRCUMSTANCES should real API keys, tokens, passwords, or credentials be committed to version control.**

### Why This Matters

- Exposed keys can be:
  - Scraped by bots within minutes
  - Used to rack up charges on your account
  - Used to access or delete your data
  - Difficult to fully remove from git history

## ✅ Security Measures in Place

### 1. Pre-Commit Hook

A pre-commit hook automatically scans staged files for secrets before allowing commits.

**What it detects:**
- OpenAI API keys (`sk-proj-*`)
- Anthropic API keys (`sk-ant-*`)
- AWS access keys (`AKIA*`)
- GitHub personal access tokens (`ghp_*`)
- Private keys (PEM files)
- Generic API key patterns

**Location:** `.git/hooks/pre-commit`

**Bypass (USE WITH CAUTION):**
```bash
git commit --no-verify  # Only use if you're certain no secrets are present
```

### 2. Gitleaks Configuration

Gitleaks is configured to scan the entire repository for secrets.

**Configuration file:** `.gitleaks.toml`

**Run manually:**
```bash
# Install gitleaks (macOS)
brew install gitleaks

# Scan the repository
gitleaks detect --verbose

# Scan specific files
gitleaks detect --source . --verbose
```

### 3. GitHub Actions CI/CD

Automated secret scanning runs on:
- Every push to main/mvp_ryanair branches
- Every pull request
- Daily at 2 AM UTC (scheduled scan)

**Workflow file:** `.github/workflows/secret-scanning.yml`

### 4. .gitignore Protection

The following patterns are excluded from git:
```
.env
*.env
.env.*
*.pem
*.key
credentials.json
.aws_credentials_reference.txt
```

## 📋 Required Setup: Environment Variables

### Step 1: Copy the Template
```bash
cp .env.example .env
```

### Step 2: Add Your Real Keys
Edit `.env` and replace placeholder values with your actual API keys:

```bash
# .env file (NEVER commit this!)
export OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
export ANTHROPIC_API_KEY=sk-ant-YOUR_ACTUAL_KEY_HERE
export TRAINING_S3_BUCKET=your-actual-bucket-name
```

### Step 3: Load Environment Variables
```bash
source .env
```

### Step 4: Verify
```bash
echo $OPENAI_API_KEY  # Should show your key
```

## 🔑 API Key Management Best Practices

### Development Environment

1. **Use separate keys for dev/prod**
   - Never use production keys in development
   - Create separate OpenAI projects for dev/staging/prod

2. **Set usage limits**
   - Configure spending limits in OpenAI dashboard
   - Set up billing alerts

3. **Restrict key permissions**
   - Use least-privilege access
   - Restrict keys to specific IPs when possible

4. **Rotate keys regularly**
   - Rotate keys every 90 days
   - Rotate immediately if exposed

### Production Environment

1. **Use secure secret management**
   ```bash
   # AWS Secrets Manager
   aws secretsmanager create-secret --name prod/openai/api-key --secret-string "sk-proj-..."

   # Or AWS SSM Parameter Store
   aws ssm put-parameter --name /prod/openai/api-key --value "sk-proj-..." --type SecureString
   ```

2. **Use IAM roles**
   - For AWS services, use IAM roles instead of access keys
   - Enable MFA for all privileged accounts

3. **Enable audit logging**
   - Track all API key usage
   - Set up alerts for unusual activity

## 🚨 What to Do If Keys Are Exposed

### Immediate Actions (Within Minutes)

1. **Revoke the exposed key immediately**
   ```bash
   # OpenAI: https://platform.openai.com/api-keys
   # Delete or disable the compromised key

   # AWS:
   aws iam delete-access-key --access-key-id AKIA...
   ```

2. **Generate a new key**
   - Create a replacement key
   - Update your `.env` file
   - Reload environment: `source .env`

3. **Check for unauthorized usage**
   - OpenAI: Check usage dashboard
   - AWS: Review CloudTrail logs
   - Check billing for unexpected charges

### Git History Cleanup (If Already Committed)

If you've committed secrets to git:

```bash
# Option 1: Use git-filter-repo (recommended)
git filter-repo --path .env --invert-paths --force

# Option 2: Use BFG Repo-Cleaner
bfg --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push to update remote
git push --force origin main
```

⚠️ **Important:**
- History rewriting changes commit hashes
- Coordinate with team before force-pushing
- Keys in git history should still be considered compromised and rotated

### Long-term Actions

1. **Post-mortem**
   - Document how the exposure happened
   - Update processes to prevent recurrence

2. **Monitor accounts**
   - Watch for fraudulent charges
   - Monitor API usage patterns

3. **Update security training**
   - Review security practices with team
   - Update onboarding documentation

## 📝 Code Review Checklist

Before approving any PR, verify:

- [ ] No API keys in code
- [ ] No hardcoded credentials
- [ ] No `.env` files committed
- [ ] No AWS credentials
- [ ] No private keys or certificates
- [ ] Secret scanning CI checks passed
- [ ] Environment variables properly documented

## 🔍 Testing Secret Detection

Test that the pre-commit hook works:

```bash
# Create a test file with a fake secret
echo 'sk-proj-test1234567890123456789012345678901234567890' > test_secret.txt

# Try to commit it
git add test_secret.txt
git commit -m "test commit"

# Should be BLOCKED by pre-commit hook

# Clean up
rm test_secret.txt
git reset
```

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [AWS Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Gitleaks Documentation](https://github.com/zricethezav/gitleaks)

## 🆘 Support

If you discover a security vulnerability or have questions:

1. **DO NOT** create a public GitHub issue
2. Contact the security team directly
3. Report the issue privately

## 📊 Security Audit Log

| Date | Action | Person | Notes |
|------|--------|--------|-------|
| 2025-10-31 | Initial security setup | Claude Code | Added pre-commit hooks, gitleaks config, CI/CD scanning |
| 2025-10-31 | API key rotation | User | Rotated exposed OpenAI key |

---

**Remember: Security is everyone's responsibility. When in doubt, ask!** 🛡️
