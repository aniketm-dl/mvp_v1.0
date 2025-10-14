# AWS Training Quick Start (5 Minutes)

Ultra-fast setup guide for training digital twin adapters on AWS.

## Prerequisites (One-Time Setup)

```bash
# 1. Install AWS CLI
brew install awscli  # macOS
# or: pip install awscli

# 2. Configure credentials
aws configure
# Enter your Access Key, Secret Key, and region (e.g., us-east-1)

# 3. Create S3 bucket (optional but recommended)
aws s3 mb s3://your-training-bucket
```

## Launch & Train (3 Commands)

### Option 1: Fully Interactive (Recommended)

```bash
# From your local machine
cd ~/mvp_v1.0
./scripts/aws/launch_training_instance.sh
```

This will:
1. Ask you to choose GPU type (g4dn.xlarge recommended)
2. Launch the instance
3. Show you the SSH command

Then SSH in and run:
```bash
# On EC2 instance
bash <(curl -s https://raw.githubusercontent.com/aniketm-dl/mvp_v1.0/main/scripts/aws/setup_training_instance.sh)
```

### Option 2: Quick CLI Launch

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type g4dn.xlarge \
  --key-name your-key-pair \
  --instance-market-options '{"MarketType":"spot"}' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100}}]'

# Get IP (wait ~30 seconds first)
INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# Connect
ssh -i ~/.ssh/your-key.pem ubuntu@$INSTANCE_IP
```

Then on EC2:
```bash
bash <(curl -s https://raw.githubusercontent.com/aniketm-dl/mvp_v1.0/main/scripts/aws/setup_training_instance.sh)
```

## Start Training

Once setup completes:

```bash
cd ~/mvp_v1.0
source venv/bin/activate

# Option 1: Simple
python scripts/aws/train_with_s3_sync.py

# Option 2: With auto-shutdown (saves money!)
python scripts/aws/train_with_s3_sync.py --auto-shutdown

# Option 3: Background with tmux
tmux new -s training
python scripts/aws/train_with_s3_sync.py --auto-shutdown
# Press Ctrl+B then D to detach
```

## Download Results

```bash
# From your local machine
aws s3 sync s3://your-bucket/trained_adapters/ \
  ~/mvp_v1.0/artifacts/llm_adapters/
```

## Costs

| GPU | Spot Price | Time | Total |
|-----|------------|------|-------|
| g4dn.xlarge | $0.18/hr | 3.5h | **$0.63** |
| g5.xlarge | $0.35/hr | 1.5h | **$0.53** |

## Cleanup

```bash
# Find your instance
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=darpan-training" \
  --query 'Reservations[0].Instances[0].InstanceId'

# Terminate it
aws ec2 terminate-instances --instance-ids i-xxxxx
```

## Troubleshooting

**Can't connect?**
```bash
# Check instance is running
aws ec2 describe-instances --instance-ids i-xxxxx

# Check security group allows SSH
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

**Training failed?**
```bash
# Check GPU
nvidia-smi

# Check logs
tail -f ~/mvp_v1.0/artifacts/training_report.json
```

**Need more help?**
See full guide: [DOCS/AWS_TRAINING_GUIDE.md](AWS_TRAINING_GUIDE.md)
