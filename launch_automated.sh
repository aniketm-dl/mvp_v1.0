#!/bin/bash
###############################################################################
# Automated AWS GPU Instance Launcher - Non-Interactive
# Pre-configured with optimal settings for Darpan Labs training
###############################################################################

set -e

# Configuration
AWS_REGION="ap-south-1"  # Mumbai region (your configured region)
INSTANCE_TYPE="g5.xlarge"  # A10G GPU, 24GB VRAM
USE_SPOT="true"
MAX_SPOT_PRICE="0.50"
KEY_NAME="darpan-training"
KEY_PATH="$HOME/darpan-training.pem"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================================================="
echo "🚀 AWS GPU INSTANCE LAUNCHER - Automated Mode"
echo "=========================================================================="
echo ""
echo "Configuration:"
echo "  Region: $AWS_REGION"
echo "  Instance: $INSTANCE_TYPE"
echo "  Type: Spot ($MAX_SPOT_PRICE/hour max)"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: $AWS_ACCOUNT${NC}"
echo ""

# Create or verify SSH key
if [ ! -f "$KEY_PATH" ]; then
    echo "Creating SSH key pair..."
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$AWS_REGION" \
        --query 'KeyMaterial' \
        --output text > "$KEY_PATH"
    chmod 400 "$KEY_PATH"
    echo -e "${GREEN}✅ Created key: $KEY_PATH${NC}"
else
    echo -e "${GREEN}✅ Using existing key: $KEY_PATH${NC}"
fi

# Get Ubuntu 22.04 Deep Learning AMI
echo ""
echo "Finding latest Deep Learning AMI..."
AMI_ID=$(aws ec2 describe-images \
    --region "$AWS_REGION" \
    --owners amazon \
    --filters "Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)*" \
              "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

if [ -z "$AMI_ID" ] || [ "$AMI_ID" == "None" ]; then
    echo -e "${YELLOW}⚠️  Deep Learning AMI not found, using standard Ubuntu 22.04${NC}"
    AMI_ID=$(aws ec2 describe-images \
        --region "$AWS_REGION" \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
                  "Name=state,Values=available" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)
fi

echo -e "${GREEN}✅ AMI: $AMI_ID${NC}"

# Create security group if needed
SG_NAME="darpan-training-sg"
echo ""
echo "Checking security group..."

SG_ID=$(aws ec2 describe-security-groups \
    --region "$AWS_REGION" \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --region "$AWS_REGION" \
        --group-name "$SG_NAME" \
        --description "Security group for Darpan Labs training instances" \
        --query 'GroupId' \
        --output text)

    # Allow SSH from anywhere
    aws ec2 authorize-security-group-ingress \
        --region "$AWS_REGION" \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

    echo -e "${GREEN}✅ Created security group: $SG_ID${NC}"
else
    echo -e "${GREEN}✅ Using existing security group: $SG_ID${NC}"
fi

# Launch instance
echo ""
echo "=========================================================================="
echo "🚀 Launching $INSTANCE_TYPE instance..."
echo "=========================================================================="
echo ""

if [ "$USE_SPOT" == "true" ]; then
    # Launch spot instance
    LAUNCH_SPEC=$(cat <<EOF
{
  "ImageId": "$AMI_ID",
  "InstanceType": "$INSTANCE_TYPE",
  "KeyName": "$KEY_NAME",
  "SecurityGroupIds": ["$SG_ID"],
  "BlockDeviceMappings": [{
    "DeviceName": "/dev/sda1",
    "Ebs": {
      "VolumeSize": 100,
      "VolumeType": "gp3",
      "DeleteOnTermination": true
    }
  }],
  "TagSpecifications": [{
    "ResourceType": "instance",
    "Tags": [
      {"Key": "Name", "Value": "darpan-training"},
      {"Key": "Project", "Value": "darpan-labs"}
    ]
  }],
  "UserData": "$(echo '#!/bin/bash
cd /home/ubuntu
git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0
' | base64 -w 0)"
}
EOF
)

    SPOT_REQUEST=$(aws ec2 request-spot-instances \
        --region "$AWS_REGION" \
        --spot-price "$MAX_SPOT_PRICE" \
        --instance-count 1 \
        --type "one-time" \
        --launch-specification "$LAUNCH_SPEC" \
        --output json)

    SPOT_REQUEST_ID=$(echo "$SPOT_REQUEST" | jq -r '.SpotInstanceRequests[0].SpotInstanceRequestId')

    echo "Waiting for spot request to be fulfilled..."
    echo "Request ID: $SPOT_REQUEST_ID"

    # Wait for spot request
    for i in {1..60}; do
        STATUS=$(aws ec2 describe-spot-instance-requests \
            --region "$AWS_REGION" \
            --spot-instance-request-ids "$SPOT_REQUEST_ID" \
            --query 'SpotInstanceRequests[0].Status.Code' \
            --output text)

        if [ "$STATUS" == "fulfilled" ]; then
            break
        elif [ "$STATUS" == "price-too-low" ] || [ "$STATUS" == "capacity-not-available" ]; then
            echo -e "${RED}❌ Spot request failed: $STATUS${NC}"
            echo "Try increasing max price or use on-demand instance"
            exit 1
        fi

        echo "Status: $STATUS (waiting...)"
        sleep 5
    done

    INSTANCE_ID=$(aws ec2 describe-spot-instance-requests \
        --region "$AWS_REGION" \
        --spot-instance-request-ids "$SPOT_REQUEST_ID" \
        --query 'SpotInstanceRequests[0].InstanceId' \
        --output text)
else
    # Launch on-demand instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --region "$AWS_REGION" \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SG_ID" \
        --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
        --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=darpan-training},{Key=Project,Value=darpan-labs}]' \
        --query 'Instances[0].InstanceId' \
        --output text)
fi

echo -e "${GREEN}✅ Instance launched: $INSTANCE_ID${NC}"

# Wait for instance to be running
echo ""
echo "Waiting for instance to start..."
aws ec2 wait instance-running \
    --region "$AWS_REGION" \
    --instance-ids "$INSTANCE_ID"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo -e "${GREEN}✅ Instance is running!${NC}"
echo ""
echo "=========================================================================="
echo "✅ INSTANCE SUCCESSFULLY LAUNCHED"
echo "=========================================================================="
echo ""
echo "Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Region: $AWS_REGION"
echo "  Type: $INSTANCE_TYPE"
echo ""
echo "=========================================================================="
echo "📝 NEXT STEPS"
echo "=========================================================================="
echo ""
echo "1. Wait 2-3 minutes for instance to finish initializing"
echo ""
echo "2. SSH into the instance:"
echo "   ssh -i $KEY_PATH ubuntu@$PUBLIC_IP"
echo ""
echo "3. On the instance, clone and setup:"
echo "   cd mvp_v1.0"
echo "   make setup-instance    # ~10 minutes"
echo "   make train            # ~90 minutes"
echo ""
echo "4. Back on your local machine:"
echo "   make download         # Download trained models"
echo "   make chat            # Interactive chat"
echo ""
echo "=========================================================================="
echo ""

# Save instance info
cat > ~/.darpan_instance_info << EOF
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
AWS_REGION=$AWS_REGION
KEY_PATH=$KEY_PATH
EOF

echo "Instance info saved to: ~/.darpan_instance_info"
echo ""
echo -e "${YELLOW}💡 To terminate the instance later:${NC}"
echo "   aws ec2 terminate-instances --region $AWS_REGION --instance-ids $INSTANCE_ID"
echo ""
