# Retraining All 18 Personas with New Core Logic

**Date:** 2025-10-15
**Purpose:** Retrain all personas with the new learned fusion, policy-first routing, and guardrails
**Estimated Time:** ~2 hours
**Estimated Cost:** ~$0.70

---

## 📋 Pre-Flight Checklist

Before starting, verify:

- [x] All code changes committed to `refactor/aws-workflow-automation` branch
- [x] Changes pushed to GitHub
- [ ] AWS credentials configured (`aws configure`)
- [ ] SSH key exists (`~/darpan-training.pem`)
- [ ] S3 bucket configured

---

## 🚀 Complete Retraining Workflow

### Option A: Automated (Recommended)

```bash
# Launch EC2, sync code, train, download
make launch
make sync-code    # Enter instance IP when prompted
# SSH to EC2 and train
# Download models
make download
```

### Option B: Step-by-Step (Full Control)

Follow the detailed steps below.

---

## Step 1: Launch EC2 GPU Instance

```bash
make launch
```

**Expected Output:**
```
📡 LAUNCHING AWS INSTANCE
...
✅ Instance launched successfully!
Instance ID: i-xxxxxxxxxxxxx
Instance IP: xx.xx.xx.xx
```

**Save the Instance IP** - you'll need it for SSH.

---

## Step 2: Sync Code to EC2

You have two options:

### Option A: Direct Sync (Faster)

```bash
make sync-code
# Enter instance IP when prompted
```

This syncs your local changes directly to EC2 without going through GitHub.

### Option B: Via GitHub (Cleaner)

```bash
# SSH to instance
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>

# Pull latest code
cd ~/mvp_v1.0
git pull origin refactor/aws-workflow-automation

# Verify changes
git log -1
```

---

## Step 3: SSH to EC2 Instance

```bash
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>
```

**First time?** The instance should already be set up. If not, run:
```bash
cd ~/mvp_v1.0
source venv/bin/activate
```

---

## Step 4: Retrain All 18 Personas

On the EC2 instance:

```bash
cd ~/mvp_v1.0
source venv/bin/activate

# Verify GPU is available
nvidia-smi

# Start training with auto-shutdown (recommended)
./darpan.py train --auto-shutdown

# OR use tmux for persistent session
tmux new -s training
./darpan.py train --auto-shutdown
# Press Ctrl+B then D to detach
```

**Training Progress:**
- 18 personas × ~5-7 minutes each = ~90-120 minutes total
- Models auto-save to S3 after each persona
- Instance auto-shuts down when complete (saves money!)

**Monitor Progress:**

From your local machine:
```bash
# Check S3 for completed models
make s3-list

# Or manually
aws s3 ls s3://your-bucket/trained_adapters/
```

---

## Step 5: Download Trained Models

**Wait for training to complete**, then on your local machine:

```bash
make download
```

This downloads all 18 trained persona adapters from S3 to `artifacts/llm_adapters/`.

**Verify download:**
```bash
ls -lh artifacts/llm_adapters/
```

You should see 18 directories (k0, k1, k2, ... k17), each containing:
- `adapter_config.json`
- `adapter_model.safetensors`

---

## Step 6: Test Persona Responses Locally

Now let's test the new personas!

### Quick Test: Chat Interface

```bash
make serve    # Start API server
make chat     # Interactive chat
```

**Try different personas:**
- Budget-conscious twin
- Premium buyer twin
- Deal-seeker twin

### Comprehensive Test: Run Test Script

Create a test script to compare responses:

```bash
python examples/test_persona_responses.py
```

I'll create this script for you.

---

## Step 7: Compare Old vs New Responses

Let's create a comparison test to see the improvements.

---

