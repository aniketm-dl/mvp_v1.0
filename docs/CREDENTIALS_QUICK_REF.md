# 🔐 Credentials Quick Reference

## Where Everything Is Stored

```
~/.aws/
  ├── credentials          ⚠️  AWS access keys (NEVER share!)
  └── config              ✅  Region settings (safe)

~/darpan-training.pem      ⚠️  SSH private key (NEVER share!)

~/.cache/huggingface/
  └── token               ⚠️  HuggingFace token (NEVER share!)

~/.aws_training_env        ✅  S3 bucket, region (safe to share)
~/.darpan_workflow_state.json  ✅  Workflow progress (safe)
```

## Quick Commands

```bash
# View AWS credentials (SENSITIVE!)
cat ~/.aws/credentials

# View AWS region
cat ~/.aws/config

# View S3 bucket
cat ~/.aws_training_env

# View SSH key location
ls -la ~/darpan-training.pem

# Test AWS connection
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://$(grep TRAINING_S3_BUCKET ~/.aws_training_env | cut -d'"' -f2)
```

## Security Checklist

- [ ] AWS credentials in `~/.aws/credentials` (permissions: 600)
- [ ] SSH key has permissions 400: `chmod 400 ~/darpan-training.pem`
- [ ] `.gitignore` blocks `*.pem`, `.env`, `credentials.json`
- [ ] No credentials committed to Git
- [ ] HuggingFace token set: `huggingface-cli whoami`

## What to Share vs. Keep Secret

### ✅ SAFE to share:
- S3 bucket name
- AWS region
- Instance type (g5.xlarge)
- Public GitHub repo URL

### ⚠️ NEVER share:
- AWS Access Key ID / Secret Key
- SSH private key (`.pem` file)
- HuggingFace token
- Anything in `~/.aws/credentials`

## Emergency: Credentials Leaked!

```bash
# 1. Delete AWS access key (AWS Console → IAM)
# 2. Create new key
aws configure

# 3. Delete SSH key from AWS
aws ec2 delete-key-pair --key-name darpan-training

# 4. Create new SSH key
aws ec2 create-key-pair --key-name darpan-training-new \
  --query 'KeyMaterial' --output text > ~/darpan-training-new.pem
chmod 400 ~/darpan-training-new.pem

# 5. Check for unauthorized usage
aws cloudtrail lookup-events --max-results 50
```

## Your Current Setup

```bash
# Check everything is configured
echo "=== AWS Credentials ==="
test -f ~/.aws/credentials && echo "✅ Found" || echo "❌ Missing"

echo "=== AWS Region ==="
aws configure get region

echo "=== SSH Key ==="
ls -la ~/darpan-training.pem 2>/dev/null && echo "✅ Found" || echo "❌ Missing"

echo "=== S3 Bucket ==="
cat ~/.aws_training_env 2>/dev/null | grep TRAINING_S3_BUCKET || echo "❌ Not set"

echo "=== HuggingFace ==="
huggingface-cli whoami 2>/dev/null || echo "❌ Not authenticated"
```

---

**Full details:** [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)
