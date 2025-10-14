# AWS Credentials & Security Guide

**IMPORTANT: This guide explains where credentials are stored and how to manage them securely.**

## 🔐 Where Credentials Are Stored

### 1. AWS Credentials (`~/.aws/`)

**Location:** `~/.aws/credentials` and `~/.aws/config`

```bash
# View AWS credentials location
ls ~/.aws/

# Files:
# - credentials    # Access keys (SENSITIVE!)
# - config         # Region and output settings
```

**Contents of `~/.aws/credentials`:**
```ini
[default]
aws_access_key_id = AKIAXXXXXXXXXXXXXXXX
aws_secret_access_key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Contents of `~/.aws/config`:**
```ini
[default]
region = us-east-1
output = json
```

⚠️ **Security:** These files contain your AWS access keys. Never commit to Git!

---

### 2. SSH Key for EC2 (`~/darpan-training.pem`)

**Location:** `~/darpan-training.pem`

**Purpose:** SSH access to EC2 training instances

**Permissions:** Must be `400` (read-only by owner)
```bash
ls -la ~/darpan-training.pem
# Should show: -r-------- (400)

# Fix if needed:
chmod 400 ~/darpan-training.pem
```

⚠️ **Security:** This is your private SSH key. Never share or commit to Git!

---

### 3. Training Environment (`~/.aws_training_env`)

**Location:** `~/.aws_training_env`

**Purpose:** Stores training-specific settings (S3 bucket, instance info)

**Example contents:**
```bash
TRAINING_S3_BUCKET=darpan-training-1760183626
INSTANCE_ID=i-0123456789abcdef0
INSTANCE_IP=54.123.45.67
REGION=us-east-1
```

✅ **Security:** This is safe to store. Contains instance info, not credentials.

---

### 4. Workflow State (`~/.darpan_workflow_state.json`)

**Location:** `~/.darpan_workflow_state.json`

**Purpose:** Tracks workflow progress (launch, setup, train, download)

**Example contents:**
```json
{
  "instance_id": "i-0123456789abcdef0",
  "instance_ip": "54.123.45.67",
  "s3_bucket": "darpan-training-1760183626",
  "setup_complete": true,
  "training_complete": true,
  "download_complete": true,
  "adapter_count": 18
}
```

✅ **Security:** Safe. Contains state info, not credentials.

---

### 5. HuggingFace Token (`~/.cache/huggingface/token`)

**Location:** `~/.cache/huggingface/token`

**Purpose:** Authenticates with HuggingFace to download models

⚠️ **Security:** This is sensitive. Don't share or commit.

---

## 🔍 Quick Credential Audit

Run this to see all credential-related files:

```bash
# Check AWS credentials
ls -la ~/.aws/

# Check SSH keys
ls -la ~/*.pem

# Check HuggingFace token
ls -la ~/.cache/huggingface/token

# Check training env
cat ~/.aws_training_env

# Check workflow state
cat ~/.darpan_workflow_state.json
```

---

## 🛡️ Security Best Practices

### 1. Never Commit Credentials

**.gitignore is configured to block:**
```
.env
*.env
*.pem
credentials.json
.aws/
```

### 2. Rotate Keys Regularly

```bash
# Every 90 days, create new AWS access keys:
# 1. Go to AWS IAM Console
# 2. Create new access key
# 3. Update ~/.aws/credentials
# 4. Delete old key

# Update credentials:
aws configure
```

### 3. Use IAM Roles on EC2 (Recommended)

Instead of storing credentials on EC2, use IAM roles:

```bash
# When launching instance, attach IAM role with:
# - AmazonEC2FullAccess (for spot instances)
# - AmazonS3FullAccess (for model storage)

# Then AWS CLI works automatically without credentials!
```

### 4. Secure SSH Key

```bash
# Always use correct permissions
chmod 400 ~/darpan-training.pem

# Never share your private key
# If compromised, delete from AWS and create new one
```

### 5. Use Environment Variables (Optional)

Instead of storing in files, use environment variables:

```bash
# Add to ~/.bashrc or ~/.zshrc
export AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX"
export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AWS_DEFAULT_REGION="us-east-1"
export TRAINING_S3_BUCKET="darpan-training-$(whoami)"
```

---

## 📋 Credential Checklist

Use this checklist to ensure security:

- [ ] `~/.aws/credentials` exists and has correct permissions (600)
- [ ] `~/.aws/config` exists with region set
- [ ] SSH key (`~/darpan-training.pem`) has permissions 400
- [ ] AWS credentials NOT committed to Git (check `.gitignore`)
- [ ] HuggingFace token stored securely
- [ ] S3 bucket name stored in `~/.aws_training_env`
- [ ] No credentials in code files (`.py`, `.sh`, etc.)

---

## 🚨 What to Do If Credentials Are Compromised

### If AWS Access Keys Are Leaked:

1. **Immediately delete the compromised keys:**
   ```bash
   # Go to AWS IAM Console → Users → Security Credentials
   # Delete the leaked access key
   ```

2. **Create new access keys:**
   ```bash
   # Create new key in AWS Console
   # Update ~/.aws/credentials
   aws configure
   ```

3. **Check for unauthorized usage:**
   ```bash
   # Check CloudTrail logs for suspicious activity
   aws cloudtrail lookup-events --max-results 50
   ```

### If SSH Key Is Leaked:

1. **Delete key pair from AWS:**
   ```bash
   aws ec2 delete-key-pair --key-name darpan-training
   ```

2. **Create new key pair:**
   ```bash
   aws ec2 create-key-pair \
     --key-name darpan-training-new \
     --query 'KeyMaterial' \
     --output text > ~/darpan-training-new.pem

   chmod 400 ~/darpan-training-new.pem
   ```

3. **Terminate any running instances that used old key:**
   ```bash
   aws ec2 terminate-instances --instance-ids i-xxxxx
   ```

---

## 📖 How Credentials Are Used in Workflow

### During `make launch`:
- Uses `~/.aws/credentials` to authenticate
- Creates EC2 instance
- Uses `~/darpan-training.pem` for SSH access

### During `make setup-instance`:
- Runs on EC2 instance
- Optionally configures AWS CLI on instance
- Can use IAM role instead of credentials

### During `make train`:
- Runs on EC2 instance
- Uses HuggingFace token to download models
- Uses AWS credentials (or IAM role) to sync to S3

### During `make download`:
- Runs on local machine
- Uses `~/.aws/credentials` to download from S3
- Reads S3 bucket from `~/.aws_training_env`

---

## 🔄 Backup Your Credentials (Securely!)

```bash
# Create encrypted backup
mkdir -p ~/secure_backup

# Backup AWS credentials
cp ~/.aws/credentials ~/secure_backup/aws_credentials.backup
cp ~/.aws/config ~/secure_backup/aws_config.backup

# Backup SSH key
cp ~/darpan-training.pem ~/secure_backup/darpan-training.pem.backup

# Encrypt the backup directory
zip -er ~/secure_backup.zip ~/secure_backup/
# (Enter a strong password)

# Store encrypted backup somewhere safe
# e.g., password manager, encrypted USB drive

# Delete unencrypted backup
rm -rf ~/secure_backup/
```

---

## ❓ FAQ

### Q: Where is my AWS password?
A: AWS doesn't use passwords for API access. You use:
- **Access Key ID** (like a username)
- **Secret Access Key** (like a password)
- Both stored in `~/.aws/credentials`

### Q: How do I view my credentials?
```bash
cat ~/.aws/credentials
cat ~/.aws/config
```

### Q: Can I share credentials with my team?
A: **NO!** Each team member should have their own AWS IAM user with separate credentials.

### Q: How do I know if my credentials are working?
```bash
# Test AWS credentials
aws sts get-caller-identity

# Should show your AWS account ID and user ARN
```

### Q: Where is my HuggingFace token?
```bash
# View token
cat ~/.cache/huggingface/token

# Or re-authenticate
huggingface-cli login
```

---

## 📝 Summary

**Credentials are stored in:**
1. `~/.aws/credentials` - AWS access keys ⚠️ SENSITIVE
2. `~/.aws/config` - AWS region settings ✅ Safe
3. `~/darpan-training.pem` - SSH private key ⚠️ SENSITIVE
4. `~/.cache/huggingface/token` - HF token ⚠️ SENSITIVE
5. `~/.aws_training_env` - Training settings ✅ Safe
6. `~/.darpan_workflow_state.json` - Workflow state ✅ Safe

**Security rules:**
- ✅ Never commit credentials to Git (use `.gitignore`)
- ✅ Use permissions 400 for SSH keys
- ✅ Use permissions 600 for credentials files
- ✅ Rotate keys every 90 days
- ✅ Use IAM roles on EC2 when possible
- ✅ Keep backups encrypted

---

**Last Updated:** 2025-10-11
**Status:** ✅ Secure by default
