# 🚀 Manual EC2 Instance Setup Instructions

## What You Need to Create

### Instance Configuration

**1. Instance Type:**
- **Type:** `g5.xlarge` (GPU instance for training)
- **Alternative if g5 not available:** `g4dn.xlarge` or even `t3.xlarge` (CPU-only, slower but works)

**2. AMI (Operating System):**
- **Ubuntu 22.04 LTS** (ami-0dee22c13ea7a9a67) or any recent Ubuntu

**3. Storage:**
- **Root Volume:** 150 GB (minimum 100 GB)
- **Type:** gp3 (for better performance)

**4. Region:**
- **ap-south-1** (Mumbai) - or any region you prefer

**5. Security Group:**
- Allow **SSH (port 22)** from your IP or anywhere
- That's all we need for training

**6. Key Pair:**
- **IMPORTANT:** Create new key pair or use existing
- **Download the .pem file** and save it to:
  - `~/darpan-training-final.pem` (on your Mac)
  - Or any location you choose (just tell me the path)

---

## Step-by-Step in AWS Console

### 1. Launch Instance
- Go to EC2 Console → Launch Instance
- Name: `darpan-persona-training`

### 2. Choose AMI
- Select **Ubuntu Server 22.04 LTS**

### 3. Choose Instance Type
- Select **g5.xlarge** (if available)
- If not: **g4dn.xlarge**
- If neither: **t3.2xlarge** (8 vCPUs, 32GB RAM - will work but slower)

### 4. Key Pair
- **Create new key pair:**
  - Name: `darpan-training-final`
  - Type: RSA
  - Format: .pem
  - **Download and save to your Mac**
- Or select existing key if you have one

### 5. Network Settings
- Default VPC is fine
- **Security Group:** Create new or use existing
  - **Rule:** SSH (port 22) from 0.0.0.0/0 (or your IP for security)

### 6. Storage
- **Size:** 150 GB
- **Type:** gp3
- **Delete on termination:** Yes (to save costs)

### 7. Advanced Details (Optional)
- Leave defaults

### 8. Launch!
- Click **Launch Instance**
- Wait ~2 minutes for it to start

---

## What to Give Me

Once the instance is running, I need:

### 1. **Instance Public IP Address**
```
Example: 13.232.146.18
```
Find this in: EC2 Console → Instances → Select your instance → Details tab → Public IPv4 address

### 2. **SSH Key Location**
```
Example: ~/darpan-training-final.pem
or: /Users/yourname/Downloads/darpan-training-final.pem
```

### 3. **Instance Details** (optional but helpful)
- Instance ID (e.g., i-0123456789abcdef)
- Instance Type (e.g., g5.xlarge)

---

## Quick Setup Commands for You

Once instance is created, run these on your Mac:

```bash
# Download the .pem file from AWS console to Downloads
# Then move it to your home directory
mv ~/Downloads/darpan-training-final.pem ~/darpan-training-final.pem

# Set correct permissions
chmod 400 ~/darpan-training-final.pem

# Test connection (replace with your instance IP)
ssh -i ~/darpan-training-final.pem ubuntu@YOUR_INSTANCE_IP

# If connection works, you're ready! Just give me:
# 1. The IP address
# 2. The key file path
```

---

## What I'll Do Once You Give Me Access

1. ✅ **Connect to instance**
2. ✅ **Install all dependencies** (PyTorch, transformers, etc.)
3. ✅ **Upload training data** (from S3)
4. ✅ **Start training all 18 personas** (~2-3 hours)
5. ✅ **Monitor progress continuously**
6. ✅ **Download models immediately** after training
7. ✅ **Verify everything** is downloaded correctly
8. ✅ **Run complete evaluation**
9. ⚠️  **Tell you to manually terminate** instance (I won't do it)

---

## Cost Estimate

- **g5.xlarge:** ~$1.00/hour
- **Training time:** ~3 hours
- **Total cost:** ~$3-4 for this run

---

## Ready to Start!

Just tell me:
```
IP: YOUR_INSTANCE_IP
Key: ~/path/to/your-key.pem
```

And I'll take it from there!

