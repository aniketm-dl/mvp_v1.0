# AWS Account Setup Guide

Quick guide to set up AWS for Darpan Labs training.

## Prerequisites

- AWS account
- Credit card
- Email access

## Steps

### 1. Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Enter email and password
4. Choose "Personal" account type
5. Add payment method
6. Verify phone number

### 2. Create IAM User

1. Go to IAM Console
2. Click "Users" → "Add User"
3. Username: `darpan-training`
4. Access: "Programmatic access"
5. Permissions: Attach policies:
   - `AmazonEC2FullAccess`
   - `AmazonS3FullAccess`
6. Download credentials CSV (save it!)

### 3. Configure AWS CLI

```bash
# Install AWS CLI
brew install awscli  # macOS
# or: pip install awscli

# Configure credentials
aws configure
# Enter Access Key ID (from CSV)
# Enter Secret Access Key (from CSV)
# Region: us-east-1
# Output: json
```

### 4. Create S3 Bucket

```bash
# Create unique bucket name
BUCKET_NAME="darpan-training-$(whoami)"

# Create bucket
aws s3 mb s3://$BUCKET_NAME

# Save for later
echo "export TRAINING_S3_BUCKET=$BUCKET_NAME" >> ~/.bashrc
source ~/.bashrc
```

### 5. Create SSH Key

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name darpan-training \
  --query 'KeyMaterial' \
  --output text > ~/darpan-training.pem

# Set permissions
chmod 400 ~/darpan-training.pem
```

### 6. Request GPU Quota (Optional)

For g5/p3 instances, you may need to request quota increase:

1. Go to Service Quotas console
2. Search for "EC2"
3. Find "Running On-Demand G instances"
4. Request increase to 4 vCPUs
5. Wait 15 minutes - 24 hours for approval

**Note:** Spot instances don't require quota!

### 7. Get HuggingFace Token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Name: `darpan-training`
4. Type: Read
5. Copy token (save it!)

## Verification

Test your setup:

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test S3 bucket
aws s3 ls s3://$TRAINING_S3_BUCKET

# Test SSH key
ls -l ~/darpan-training.pem
```

## Cost Management

### Set Budget Alert

```bash
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json
```

Create `budget.json`:
```json
{
  "BudgetName": "darpan-training-budget",
  "BudgetLimit": {
    "Amount": "10",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

### Monitor Costs

```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## Troubleshooting

### "Access Denied"
- Check IAM permissions
- Verify credentials: `aws configure list`

### "Bucket already exists"
- Use unique name: `darpan-training-$(date +%s)`

### "GPU quota exceeded"
- Use spot instances (no quota needed)
- Or request quota increase

## Next Steps

Once setup is complete:

```bash
# Launch training
make workflow

# Or step by step
make launch
```

See [TRAINING.md](TRAINING.md) for full training guide.

---

**Estimated setup time:** 10-15 minutes
**Cost:** $0 (just setup, no training yet)
