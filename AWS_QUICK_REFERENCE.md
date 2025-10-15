# AWS Quick Reference Card

## 🔑 Essential Commands

### Check AWS Status
```bash
aws sts get-caller-identity        # Verify credentials
aws configure get region            # Check region
aws s3 ls                          # List all buckets
```

### Training Bucket
```bash
export TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra
aws s3 ls s3://$TRAINING_S3_BUCKET/
```

### S3 Operations
```bash
# Upload to S3
aws s3 sync ./artifacts/llm_adapters/ s3://$TRAINING_S3_BUCKET/trained_adapters/

# Download from S3
aws s3 sync s3://$TRAINING_S3_BUCKET/trained_adapters/ ./artifacts/llm_adapters/

# Check bucket size
aws s3 ls s3://$TRAINING_S3_BUCKET/ --recursive --human-readable --summarize
```

## 📍 Key Information

**Account:** aniketm (730088663439)
**Region:** ap-south-1 (Mumbai)
**Bucket:** darpan-training-aniketniranjanmishra

## 🚀 Training Workflow

```bash
# Activate environment
cd "/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"
source venv/bin/activate

# Full automated workflow
make workflow

# Or step-by-step
make launch              # Launch AWS instance
make setup-instance      # Run on EC2: setup environment
make train              # Run on EC2: train models (~90 min)
make download           # Download trained models
make chat               # Interactive chat with personas
```

## 📊 Monitoring

```bash
make workflow-status    # Check progress
make cost-status       # AWS costs
make s3-list          # S3 contents
```

## 📁 Important Files

**Credentials:** `.aws_credentials_reference.txt`
**Setup Doc:** `AWS_SETUP_COMPLETE.md`
**Environment:** `.env`
**This Card:** `AWS_QUICK_REFERENCE.md`

## ⚠️ Security Notes

- Never commit `.env` or credentials files
- Keep `.aws_credentials_reference.txt` private
- Files are in `.gitignore` for safety

## 💡 Quick Tips

```bash
# Cost tracking
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics UnblendedCost

# Instance pricing (g5.xlarge in Mumbai)
aws ec2 describe-spot-price-history \
  --instance-types g5.xlarge \
  --region ap-south-1 \
  --max-results 1

# List EC2 instances
aws ec2 describe-instances \
  --region ap-south-1 \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]' \
  --output table
```

---

**Last Updated:** 2025-10-14
**Status:** ✅ All systems ready
