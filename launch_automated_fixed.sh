#!/bin/bash
set -e

# Configuration
AWS_REGION="ap-south-1"
INSTANCE_TYPE="g5.xlarge"
MAX_SPOT_PRICE="0.50"
KEY_NAME="darpan-training"
KEY_PATH="$HOME/darpan-training.pem"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================================================="
echo "🚀 AWS GPU INSTANCE LAUNCHER - Automated"
echo "=========================================================================="
echo "Region: $AWS_REGION | Instance: $INSTANCE_TYPE | Type: Spot"
echo ""

# Verify key exists or create
if [ ! -f "$KEY_PATH" ]; then
    echo "Creating SSH key pair..."
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$AWS_REGION" \
        --query 'KeyMaterial' \
        --output text > "$KEY_PATH" 2>/dev/null || {
        echo "Key pair exists in AWS, downloading..."
        # Key exists in AWS but not locally - need to use existing or create new with different name
        KEY_NAME="darpan-training-$(date +%s)"
        aws ec2 create-key-pair \
            --key-name "$KEY_NAME" \
            --region "$AWS_REGION" \
            --query 'KeyMaterial' \
            --output text > "$KEY_PATH"
    }
    chmod 400 "$KEY_PATH"
fi
echo -e "${GREEN}✅ SSH Key: $KEY_PATH${NC}"

# Get latest Ubuntu Deep Learning AMI
echo "Finding AMI..."
AMI_ID=$(aws ec2 describe-images \
    --region "$AWS_REGION" \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)
echo -e "${GREEN}✅ AMI: $AMI_ID${NC}"

# Get or create security group
SG_NAME="darpan-training-sg"
SG_ID=$(aws ec2 describe-security-groups --region "$AWS_REGION" --filters "Name=group-name,Values=$SG_NAME" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")
if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    SG_ID=$(aws ec2 create-security-group --region "$AWS_REGION" --group-name "$SG_NAME" --description "Darpan training" --query 'GroupId' --output text)
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 2>/dev/null || true
fi
echo -e "${GREEN}✅ Security Group: $SG_ID${NC}"

# Launch spot instance
echo ""
echo "🚀 Launching instance..."
LAUNCH_SPEC=$(cat <<EOF
{
  "ImageId": "$AMI_ID",
  "InstanceType": "$INSTANCE_TYPE",
  "KeyName": "$KEY_NAME",
  "SecurityGroupIds": ["$SG_ID"],
  "BlockDeviceMappings": [{"DeviceName": "/dev/sda1","Ebs": {"VolumeSize": 100,"VolumeType": "gp3"}}],
  "TagSpecifications": [{"ResourceType": "instance","Tags": [{"Key": "Name","Value": "darpan-training"}]}]
}
EOF
)

SPOT_REQUEST=$(aws ec2 request-spot-instances \
    --region "$AWS_REGION" \
    --spot-price "$MAX_SPOT_PRICE" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification "$LAUNCH_SPEC")

SPOT_REQUEST_ID=$(echo "$SPOT_REQUEST" | python3 -c "import sys,json; print(json.load(sys.stdin)['SpotInstanceRequests'][0]['SpotInstanceRequestId'])")
echo "Spot Request: $SPOT_REQUEST_ID"
echo "Waiting for fulfillment..."

# Wait for spot request
for i in {1..60}; do
    STATUS=$(aws ec2 describe-spot-instance-requests --region "$AWS_REGION" --spot-instance-request-ids "$SPOT_REQUEST_ID" --query 'SpotInstanceRequests[0].Status.Code' --output text)
    if [ "$STATUS" == "fulfilled" ]; then
        break
    elif [ "$STATUS" == "price-too-low" ] || [ "$STATUS" == "capacity-not-available" ]; then
        echo -e "${RED}❌ Spot request failed: $STATUS${NC}"
        exit 1
    fi
    echo "Status: $STATUS"
    sleep 5
done

INSTANCE_ID=$(aws ec2 describe-spot-instance-requests --region "$AWS_REGION" --spot-instance-request-ids "$SPOT_REQUEST_ID" --query 'SpotInstanceRequests[0].InstanceId' --output text)
echo -e "${GREEN}✅ Instance: $INSTANCE_ID${NC}"

# Wait for running
echo "Waiting for instance to start..."
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

PUBLIC_IP=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "=========================================================================="
echo "✅ INSTANCE LAUNCHED SUCCESSFULLY"
echo "=========================================================================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "SSH Command:"
echo "  ssh -i $KEY_PATH ubuntu@$PUBLIC_IP"
echo ""
echo "Next Steps:"
echo "  1. Wait 2-3 min for instance to initialize"
echo "  2. SSH into instance"
echo "  3. Run: cd mvp_v1.0 && make setup-instance && make train"
echo "=========================================================================="

# Save info
cat > ~/.darpan_instance_info << EOF
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
AWS_REGION=$AWS_REGION
KEY_PATH=$KEY_PATH
EOF
