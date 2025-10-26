#!/bin/bash
###############################################################################
# Launch AWS GPU Instance for Training - Interactive Script
#
# This script helps you launch an AWS EC2 GPU instance with optimal settings
# for training Darpan Labs digital twin adapters.
#
# Usage:
#   chmod +x scripts/aws/launch_training_instance.sh
#   ./scripts/aws/launch_training_instance.sh
###############################################################################

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================================================="
echo "🚀 AWS GPU INSTANCE LAUNCHER - Darpan Labs Training"
echo "=========================================================================="
echo ""

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    echo "Please install AWS CLI first:"
    echo "  macOS: brew install awscli"
    echo "  Linux: pip install awscli"
    echo "  Then run: aws configure"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "   Account: $AWS_ACCOUNT"
echo ""

# Step 1: Select Region
echo "=========================================================================="
echo "📍 Step 1: Select AWS Region"
echo "=========================================================================="
echo ""
echo "Popular regions for GPU instances:"
echo "  1. us-east-1 (N. Virginia) - Usually cheapest"
echo "  2. us-east-2 (Ohio)"
echo "  3. us-west-2 (Oregon)"
echo "  4. eu-west-1 (Ireland)"
echo "  5. ap-southeast-1 (Singapore)"
echo ""
read -p "Select region [1-5] or enter custom (default: us-east-1): " REGION_CHOICE

case $REGION_CHOICE in
    2) AWS_REGION="us-east-2" ;;
    3) AWS_REGION="us-west-2" ;;
    4) AWS_REGION="eu-west-1" ;;
    5) AWS_REGION="ap-southeast-1" ;;
    "") AWS_REGION="us-east-1" ;;
    1) AWS_REGION="us-east-1" ;;
    *) AWS_REGION="$REGION_CHOICE" ;;
esac

echo -e "${GREEN}Selected region: $AWS_REGION${NC}"
echo ""

# Step 2: Select Instance Type
echo "=========================================================================="
echo "🎮 Step 2: Select GPU Instance Type"
echo "=========================================================================="
echo ""
echo "Recommended options:"
echo ""
echo "  1. g4dn.xlarge (T4, 16GB VRAM) ⭐ RECOMMENDED"
echo "     • Cost: ~\$0.18/hour (spot), \$0.526/hour (on-demand)"
echo "     • Training time: ~3.5 hours"
echo "     • Total cost: ~\$0.63 (spot)"
echo ""
echo "  2. g5.xlarge (A10G, 24GB VRAM) ⚡ FASTER"
echo "     • Cost: ~\$0.35/hour (spot), \$1.006/hour (on-demand)"
echo "     • Training time: ~1.5 hours"
echo "     • Total cost: ~\$0.53 (spot)"
echo ""
echo "  3. p3.2xlarge (V100, 16GB VRAM) 🚀 FASTEST"
echo "     • Cost: ~\$1.00/hour (spot), \$3.06/hour (on-demand)"
echo "     • Training time: ~1 hour"
echo "     • Total cost: ~\$1.00 (spot)"
echo ""
read -p "Select instance type [1-3] (default: 1): " INSTANCE_CHOICE

case $INSTANCE_CHOICE in
    2) INSTANCE_TYPE="g5.xlarge"; SPOT_PRICE="0.50" ;;
    3) INSTANCE_TYPE="p3.2xlarge"; SPOT_PRICE="1.50" ;;
    "") INSTANCE_TYPE="g4dn.xlarge"; SPOT_PRICE="0.25" ;;
    1) INSTANCE_TYPE="g4dn.xlarge"; SPOT_PRICE="0.25" ;;
    *) INSTANCE_TYPE="$INSTANCE_CHOICE"; SPOT_PRICE="0.50" ;;
esac

echo -e "${GREEN}Selected instance: $INSTANCE_TYPE${NC}"
echo ""

# Step 3: Spot vs On-Demand
echo "=========================================================================="
echo "💰 Step 3: Pricing Model"
echo "=========================================================================="
echo ""
echo "  1. Spot Instance (RECOMMENDED) - 70% cheaper"
echo "     • Can be interrupted if AWS needs capacity"
echo "     • Training auto-resumes from last completed persona"
echo "     • Max price: \$$SPOT_PRICE/hour"
echo ""
echo "  2. On-Demand - Guaranteed, more expensive"
echo "     • Never interrupted"
echo "     • ~3x more expensive"
echo ""
read -p "Select pricing [1=spot, 2=on-demand] (default: 1): " PRICING_CHOICE

if [ "$PRICING_CHOICE" == "2" ]; then
    USE_SPOT="false"
    echo -e "${YELLOW}Using On-Demand pricing${NC}"
else
    USE_SPOT="true"
    echo -e "${GREEN}Using Spot pricing (max \$$SPOT_PRICE/hour)${NC}"
fi
echo ""

# Step 4: Key Pair
echo "=========================================================================="
echo "🔑 Step 4: SSH Key Pair"
echo "=========================================================================="
echo ""

# List existing key pairs
EXISTING_KEYS=$(aws ec2 describe-key-pairs --region $AWS_REGION --query 'KeyPairs[].KeyName' --output text 2>/dev/null || echo "")

if [ ! -z "$EXISTING_KEYS" ]; then
    echo "Existing key pairs in $AWS_REGION:"
    for key in $EXISTING_KEYS; do
        echo "  • $key"
    done
    echo ""
fi

read -p "Enter key pair name (or 'new' to create one) [default: darpan-training]: " KEY_NAME
KEY_NAME=${KEY_NAME:-darpan-training}

if [ "$KEY_NAME" == "new" ]; then
    read -p "Enter name for new key pair: " NEW_KEY_NAME
    KEY_NAME=$NEW_KEY_NAME

    echo "Creating new key pair: $KEY_NAME"
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $AWS_REGION \
        --query 'KeyMaterial' \
        --output text > ~/${KEY_NAME}.pem

    chmod 400 ~/${KEY_NAME}.pem
    echo -e "${GREEN}✅ Key pair created: ~/${KEY_NAME}.pem${NC}"
    echo -e "${YELLOW}⚠️  Keep this file safe! You need it to connect to the instance${NC}"
else
    # Check if key exists
    if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $AWS_REGION &>/dev/null; then
        echo -e "${YELLOW}⚠️  Key pair '$KEY_NAME' not found in $AWS_REGION${NC}"
        read -p "Create it now? [Y/n]: " CREATE_KEY
        if [ "$CREATE_KEY" != "n" ]; then
            aws ec2 create-key-pair \
                --key-name $KEY_NAME \
                --region $AWS_REGION \
                --query 'KeyMaterial' \
                --output text > ~/${KEY_NAME}.pem
            chmod 400 ~/${KEY_NAME}.pem
            echo -e "${GREEN}✅ Key pair created: ~/${KEY_NAME}.pem${NC}"
        else
            echo -e "${RED}❌ Cannot launch instance without key pair${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Using existing key pair: $KEY_NAME${NC}"
    fi
fi
echo ""

# Step 5: Storage Size
echo "=========================================================================="
echo "💾 Step 5: Storage Configuration"
echo "=========================================================================="
echo ""
echo "Recommended: 100 GB (enough for model, data, and training)"
read -p "Enter storage size in GB [default: 100]: " STORAGE_SIZE
STORAGE_SIZE=${STORAGE_SIZE:-100}
echo -e "${GREEN}Storage: ${STORAGE_SIZE}GB gp3 EBS${NC}"
echo ""

# Step 6: Get AMI
echo "=========================================================================="
echo "📀 Step 6: Selecting AMI..."
echo "=========================================================================="
echo ""

# Try to find Deep Learning AMI
echo "Looking for Deep Learning AMI (has CUDA pre-installed)..."
DL_AMI=$(aws ec2 describe-images \
    --owners amazon \
    --region $AWS_REGION \
    --filters "Name=name,Values=Deep Learning AMI GPU PyTorch*Ubuntu*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$DL_AMI" ] && [ "$DL_AMI" != "None" ]; then
    echo -e "${GREEN}Found Deep Learning AMI: $DL_AMI${NC}"
    read -p "Use this AMI? (has CUDA pre-installed) [Y/n]: " USE_DL_AMI
    if [ "$USE_DL_AMI" == "n" ]; then
        DL_AMI=""
    else
        AMI_ID=$DL_AMI
    fi
fi

# Fallback to Ubuntu 22.04
if [ -z "$AMI_ID" ]; then
    echo "Using Ubuntu 22.04 LTS (will install CUDA during setup)..."
    AMI_ID=$(aws ec2 describe-images \
        --owners 099720109477 \
        --region $AWS_REGION \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
        --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
        --output text)

    if [ -z "$AMI_ID" ]; then
        echo -e "${RED}❌ Could not find suitable AMI${NC}"
        exit 1
    fi
    echo -e "${GREEN}AMI: $AMI_ID (Ubuntu 22.04)${NC}"
fi
echo ""

# Step 7: Security Group
echo "=========================================================================="
echo "🔒 Step 7: Security Group (Firewall)"
echo "=========================================================================="
echo ""

SG_NAME="darpan-training-sg"
echo "Checking for security group: $SG_NAME"

# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs --region $AWS_REGION --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)

# Check if security group exists
SG_ID=$(aws ec2 describe-security-groups \
    --region $AWS_REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SG_NAME \
        --description "Security group for Darpan training instances" \
        --vpc-id $VPC_ID \
        --region $AWS_REGION \
        --query 'GroupId' \
        --output text)

    # Allow SSH from anywhere (you can restrict this to your IP)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --region $AWS_REGION \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        >/dev/null

    echo -e "${GREEN}✅ Security group created: $SG_ID${NC}"
else
    echo -e "${GREEN}✅ Using existing security group: $SG_ID${NC}"
fi
echo ""

# Step 8: Review and Launch
echo "=========================================================================="
echo "📋 Step 8: Review Configuration"
echo "=========================================================================="
echo ""
echo "  Region:         $AWS_REGION"
echo "  Instance Type:  $INSTANCE_TYPE"
echo "  Pricing:        $([ "$USE_SPOT" == "true" ] && echo "Spot (max \$$SPOT_PRICE/hr)" || echo "On-Demand")"
echo "  AMI:            $AMI_ID"
echo "  Key Pair:       $KEY_NAME"
echo "  Storage:        ${STORAGE_SIZE}GB gp3"
echo "  Security Group: $SG_ID"
echo ""

read -p "Launch instance with these settings? [Y/n]: " CONFIRM
if [ "$CONFIRM" == "n" ]; then
    echo "Launch cancelled."
    exit 0
fi

# Step 9: Launch Instance
echo ""
echo "=========================================================================="
echo "🚀 Step 9: Launching Instance..."
echo "=========================================================================="
echo ""

# Build launch command
if [ "$USE_SPOT" == "true" ]; then
    INSTANCE_ID=$(aws ec2 run-instances \
        --region $AWS_REGION \
        --image-id $AMI_ID \
        --instance-type $INSTANCE_TYPE \
        --key-name $KEY_NAME \
        --security-group-ids $SG_ID \
        --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$STORAGE_SIZE,\"VolumeType\":\"gp3\"}}]" \
        --instance-market-options "{\"MarketType\":\"spot\",\"SpotOptions\":{\"MaxPrice\":\"$SPOT_PRICE\",\"SpotInstanceType\":\"one-time\"}}" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=mvp_opera_do_not_delete},{Key=Project,Value=darpan-labs}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
else
    INSTANCE_ID=$(aws ec2 run-instances \
        --region $AWS_REGION \
        --image-id $AMI_ID \
        --instance-type $INSTANCE_TYPE \
        --key-name $KEY_NAME \
        --security-group-ids $SG_ID \
        --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$STORAGE_SIZE,\"VolumeType\":\"gp3\"}}]" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=mvp_opera_do_not_delete},{Key=Project,Value=darpan-labs}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
fi

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}❌ Failed to launch instance${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Instance launched: $INSTANCE_ID${NC}"
echo ""
echo "Waiting for instance to start..."

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $AWS_REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "=========================================================================="
echo "✨ Instance Ready!"
echo "=========================================================================="
echo ""
echo -e "${GREEN}Instance is running!${NC}"
echo ""
echo "  Instance ID:  $INSTANCE_ID"
echo "  Public IP:    $PUBLIC_IP"
echo "  Region:       $AWS_REGION"
echo "  Type:         $INSTANCE_TYPE"
echo ""
echo "=========================================================================="
echo "📝 Next Steps"
echo "=========================================================================="
echo ""
echo "1. Connect to the instance:"
echo -e "   ${BLUE}ssh -i ~/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}${NC}"
echo ""
echo "2. Download and run setup script:"
echo "   wget https://raw.githubusercontent.com/aniketm-dl/mvp_v1.0/main/scripts/aws/setup_training_instance.sh"
echo "   chmod +x setup_training_instance.sh"
echo "   ./setup_training_instance.sh"
echo ""
echo "3. Or use one-liner:"
echo "   bash <(curl -s https://raw.githubusercontent.com/aniketm-dl/mvp_v1.0/main/scripts/aws/setup_training_instance.sh)"
echo ""
echo "=========================================================================="
echo "💡 Useful Commands"
echo "=========================================================================="
echo ""
echo "Connect to instance:"
echo "  ssh -i ~/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "Check instance status:"
echo "  aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "Stop instance (keeps data, stops billing):"
echo "  aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "Start stopped instance:"
echo "  aws ec2 start-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "Terminate instance (DELETES EVERYTHING):"
echo "  aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "=========================================================================="
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Don't forget to terminate the instance when done!${NC}"
echo ""

# Save instance info to file
cat > ~/.darpan_last_instance.sh << EOF
# Last launched Darpan training instance
export INSTANCE_ID="$INSTANCE_ID"
export PUBLIC_IP="$PUBLIC_IP"
export AWS_REGION="$AWS_REGION"
export KEY_NAME="$KEY_NAME"
export INSTANCE_TYPE="$INSTANCE_TYPE"

# Quick commands
alias darpan-ssh='ssh -i ~/\${KEY_NAME}.pem ubuntu@\${PUBLIC_IP}'
alias darpan-stop='aws ec2 stop-instances --instance-ids \$INSTANCE_ID --region \$AWS_REGION'
alias darpan-start='aws ec2 start-instances --instance-ids \$INSTANCE_ID --region \$AWS_REGION'
alias darpan-terminate='aws ec2 terminate-instances --instance-ids \$INSTANCE_ID --region \$AWS_REGION'
alias darpan-status='aws ec2 describe-instances --instance-ids \$INSTANCE_ID --region \$AWS_REGION --query "Reservations[0].Instances[0].[State.Name,PublicIpAddress]" --output table'
EOF

echo "Instance info saved to: ~/.darpan_last_instance.sh"
echo "Load with: source ~/.darpan_last_instance.sh"
echo ""
