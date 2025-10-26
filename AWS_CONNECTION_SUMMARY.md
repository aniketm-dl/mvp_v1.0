# AWS EC2 Connection Details - OPeRA Persona Discovery

## 🔑 **AWS Instance Connection Details**

### **Instance Information**
- **Instance ID**: `i-04af939613450e42a`
- **Public IP**: `3.108.237.6`
- **Instance Type**: `g5.xlarge` (24GB VRAM)
- **Region**: `ap-south-1` (Mumbai)
- **Status**: `Running`

### **SSH Connection**
```bash
ssh -i ~/darpan-training-new.pem ubuntu@3.108.237.6
```

### **SSH Key Details**
- **Local Path**: `/Users/aniketniranjanmishra/darpan-training-new.pem`
- **Permissions**: `400` (read-only for owner)
- **Key Name in AWS**: `darpan-training-new`

### **AWS Configuration**
- **Account**: `730088663439` (aniketm)
- **Region**: `ap-south-1`
- **S3 Bucket**: `darpan-training-aniketniranjanmishra`

## 🛠️ **Current Setup Status**

### ✅ **Installed & Ready**
- NVIDIA drivers (580.65.06)
- CUDA toolkit (12.4)
- Python 3.10
- AWS CLI v2.31.16
- All Python dependencies installed
- Git configured with PAT token

### 📁 **Repository Status**
- **Repository**: `mvp_v1.0` cloned from `aniketm-dl/mvp_v1.0`
- **Branch**: `refactor/aws-workflow-automation`
- **Location**: `/home/ubuntu/mvp_v1.0/`
- **Status**: Up to date with all persona discovery work

## 🎯 **Completed Work on AWS**

### ✅ **OPeRA Dataset**
- Downloaded from Hugging Face (`NEU-HAI/OPeRA`)
- 437 shopping sessions from 49 users
- 4,864 actions with rationales
- Stored in: `DATA/OPeRA/processed/`

### ✅ **Persona Discovery**
- Created 18 distinct personas via K-Means clustering
- 256-D embeddings generated
- Results saved in: `artifacts/encoder/` and `artifacts/discovery/`

### 📊 **Key Output Files**
```
/home/ubuntu/mvp_v1.0/
├── artifacts/
│   ├── encoder/embeddings.parquet     # 256-D embeddings with persona labels
│   └── discovery/labels.pkl           # 18 persona clustering results
├── DATA/OPeRA/processed/              # Original OPeRA dataset
└── OPERA_PERSONA_DISCOVERY_SUMMARY.md # Complete project summary
```

## 🚀 **Ready for Next Steps**

### **Immediate Commands to Run**
```bash
# Connect to AWS
ssh -i ~/darpan-training-new.pem ubuntu@3.108.237.6

# Navigate to project
cd mvp_v1.0

# Verify persona discovery results
python3 -c "
import pandas as pd
import pickle
emb_df = pd.read_parquet('artifacts/encoder/embeddings.parquet')
with open('artifacts/discovery/labels.pkl', 'rb') as f:
    labels_data = pickle.load(f)
print(f'Personas: {labels_data[\"n_clusters\"]}')
print(f'Sessions: {len(emb_df)}')
print(f'Users: {emb_df[\"user_id\"].nunique()}')
"
```

### **Next Phase Ready**
- ✅ 18 personas discovered and labeled
- ✅ 256-D embeddings compatible with existing system
- ✅ All dependencies installed
- ✅ GPU available for training
- ✅ Repository up to date

## 📋 **Quick Start for New Chat**

**Connection Command:**
```bash
ssh -i ~/darpan-training-new.pem ubuntu@3.108.237.6
```

**Project Location:**
```bash
cd mvp_v1.0
```

**Status Check:**
```bash
ls -la artifacts/encoder/embeddings.parquet
ls -la artifacts/discovery/labels.pkl
cat OPERA_PERSONA_DISCOVERY_SUMMARY.md
```

## 🎉 **Current Status**
- **AWS Instance**: ✅ Running and accessible
- **Repository**: ✅ Cloned and up to date
- **Dependencies**: ✅ All installed
- **OPeRA Data**: ✅ Downloaded and processed
- **Persona Discovery**: ✅ 18 personas created
- **Ready for**: ✅ Persona training and interaction development

---

**Next Chat Context**: "I have an AWS g5.xlarge instance running with the OPeRA persona discovery pipeline completed. 18 personas are ready for training. Connect using the SSH details above and proceed with [specific next step]."
