# 🎯 Quick Reference: Persona Evaluation System

## ⚡ Most Common Commands

### Check Training Status
```bash
./check_training_status.sh
```

### Complete Evaluation (After Training)
```bash
./scripts/run_complete_evaluation.sh \
    --version v1.0 \
    --sprint "Sprint 1"
```

### Compare Two Versions
```bash
python scripts/compare_persona_versions.py v1.0 v2.0 --detailed
```

### View All Version Trends
```bash
python scripts/compare_persona_versions.py --trend-analysis
```

---

## 📊 Key Metrics

| Metric | Target | Weight |
|--------|--------|--------|
| Overall Score | ≥0.70 | - |
| Persona Consistency | ≥0.80 | 25% |
| Response Quality | ≥0.70 | 25% |
| Differentiation | ≥0.50 | 20% |
| Domain Expertise | ≥0.75 | 15% |
| Multi-turn Coherence | ≥0.35 | 15% |

---

## 🎯 Quality Gates

| Level | Overall Score | Pass Rate |
|-------|---------------|-----------|
| **Production** | ≥0.80 | ≥90% |
| **Recommended** | ≥0.70 | ≥80% |
| **Minimum** | ≥0.60 | ≥70% |
| **Failed** | <0.60 | <70% |

---

## 🔄 Workflow After Training

```bash
# 1. Training completes (auto-download running)
# 2. Models downloaded automatically

# 3. Run complete evaluation
./scripts/run_complete_evaluation.sh \
    --version auto_YYYYMMDD_HHMMSS \
    --sprint "Sprint N"

# 4. Review HTML report (opens automatically)

# 5. If RECOMMENDED or APPROVED:
cd trained_models && ln -sf {version} latest

# 6. If needs improvement:
# - Review recommendations in report
# - Make improvements
# - Retrain
```

---

## 📁 Report Locations

```bash
# Test results
reports/tests/test_report_{version}_{timestamp}.md

# Quality assessment
reports/persona_evaluation/{version}_{timestamp}.md

# Version comparison
reports/comparisons/comparison_{v1}_vs_{v2}_{timestamp}.md

# Sprint review (HTML)
reports/sprints/Sprint_N_{version}.html  # ← Open this one!
```

---

## 🛠️ Individual Tools

### Testing
```bash
# All personas
python scripts/test_all_personas.py --version v1.0

# Quick test (3 personas)
python scripts/test_all_personas.py --quick

# Specific personas
python scripts/test_all_personas.py --personas bargain_hunter premium_loyalist
```

### Assessment
```bash
# Full assessment
python scripts/persona_assessment.py --version v1.0

# Quick assessment
python scripts/persona_assessment.py --quick

# Custom output
python scripts/persona_assessment.py --version v1.0 --output custom/path/
```

### Comparison
```bash
# Basic comparison
python scripts/compare_persona_versions.py v1.0 v2.0

# Detailed with per-persona breakdown
python scripts/compare_persona_versions.py v1.0 v2.0 --detailed

# Historical trends
python scripts/compare_persona_versions.py --trend-analysis

# Save to custom location
python scripts/compare_persona_versions.py v1.0 v2.0 --output reports/custom/
```

### Sprint Report
```bash
# Basic sprint report
python scripts/generate_sprint_report.py --sprint "Sprint 1" --version v1.0

# With comparison
python scripts/generate_sprint_report.py \
    --sprint "Sprint 2" \
    --version v2.0 \
    --previous v1.0

# Custom output
python scripts/generate_sprint_report.py \
    --sprint "Sprint 1" \
    --version v1.0 \
    --output custom/path/
```

---

## 🚨 Troubleshooting

### "Version not found"
```bash
# List available versions
ls trained_models/

# Or check with trend analysis
python scripts/compare_persona_versions.py --trend-analysis
```

### "No evaluation results"
```bash
# Run assessment first
python scripts/persona_assessment.py --version v1.0

# Then comparison will work
python scripts/compare_persona_versions.py v1.0 v2.0
```

### "Tests failing"
```bash
# Check specific failures
cat reports/tests/test_report_v1.0_latest.json | grep -A 5 '"passed": false'

# Or check the markdown report
cat reports/tests/test_report_v1.0_latest.md
```

### "Evaluation too slow"
```bash
# Use quick mode
python scripts/persona_assessment.py --quick
python scripts/test_all_personas.py --quick
```

---

## 📊 Interpreting Results

### Deployment Recommendations

| Message | Meaning | Action |
|---------|---------|--------|
| ✅ RECOMMENDED | Significant improvement | Deploy now |
| ✓ APPROVED | Minor improvement | Safe to deploy |
| = NEUTRAL | No major changes | Optional |
| ⚠️ REVIEW NEEDED | Some regressions | Review first |
| 🚫 DO NOT DEPLOY | Critical issues | Don't deploy |

### Score Interpretation

| Score Range | Grade | Status |
|-------------|-------|--------|
| 0.80 - 1.00 | A | Excellent |
| 0.70 - 0.79 | B | Good |
| 0.60 - 0.69 | C | Acceptable |
| 0.50 - 0.59 | D | Poor |
| < 0.50 | F | Failed |

---

## 🎯 Current Status (Live)

```bash
# Training progress
./check_training_status.sh

# Auto-download monitor
tail -20 auto_download.log

# List versions
ls -la trained_models/

# Latest evaluation
ls -lt reports/persona_evaluation/ | head -5
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `PERSONA_EVALUATION_GUIDE.md` | Complete usage guide |
| `PERSONA_ASSESSMENT_SYSTEM_SUMMARY.md` | System architecture |
| `IMPLEMENTATION_COMPLETE.md` | What was built |
| `QUICK_REFERENCE_EVALUATION.md` | This file - quick reference |
| `CONFIGS/persona_evaluation_metrics.yaml` | Metrics definitions |

---

## ⏰ Typical Timeline

| Activity | Time | Status |
|----------|------|--------|
| Training (18 personas) | ~2-3 hours | 🔄 In progress (61%) |
| Auto-download | ~5-10 min | ⏸️ Waiting |
| Complete evaluation | ~3-5 min | ⏸️ Waiting |
| Review reports | ~5-10 min | ⏸️ Waiting |
| **Total** | **~2.5-3.5 hours** | **35 min remaining** |

---

## 🎊 One-Liners

```bash
# Status check
./check_training_status.sh && tail -5 auto_download.log

# Full evaluation when ready
./scripts/run_complete_evaluation.sh --version v1.0 --sprint "Sprint 1"

# Compare and decide
python scripts/compare_persona_versions.py v1.0 v2.0 --detailed && echo "Review the recommendation above!"

# Deploy if approved
cd trained_models && ln -sf v2.0 latest && echo "✅ Deployed!"

# Quick health check
python scripts/test_all_personas.py --quick && python scripts/persona_assessment.py --quick
```

---

## 🔔 Notifications

### Check if training done
```bash
# Method 1: Check status
./check_training_status.sh

# Method 2: Check auto-download log
tail auto_download.log

# Method 3: Check for downloaded models
ls -la trained_models/auto_*/
```

---

## 🎯 Sprint Checklist

After each training run:

- [ ] Wait for training completion (~35 min remaining)
- [ ] Verify auto-download succeeded
- [ ] Run complete evaluation workflow
- [ ] Review HTML sprint report
- [ ] Check quality gates (passed/failed)
- [ ] Review recommendations
- [ ] Make deployment decision
- [ ] Update `latest` symlink (if deploying)
- [ ] Plan next sprint improvements
- [ ] Archive reports for records

---

## 🚀 Next Steps (When Training Done)

```bash
# 1. Check completion
./check_training_status.sh
# Should show: 18/18 personas completed

# 2. Verify download
ls trained_models/auto_*/
# Should see: adapters/, metadata/, configs/

# 3. Run evaluation (ONE COMMAND!)
./scripts/run_complete_evaluation.sh \
    --version auto_20241016_XXXXXX \
    --sprint "Sprint 1 - Baseline"

# 4. HTML report opens automatically in browser
# Read it, get recommendations, make decision!

# 5. If approved, deploy
cd trained_models && ln -sf auto_20241016_XXXXXX latest
```

---

**That's it! Everything in one place.** 🎊

**For detailed info:** See `PERSONA_EVALUATION_GUIDE.md`
**For system details:** See `PERSONA_ASSESSMENT_SYSTEM_SUMMARY.md`
**For what was built:** See `IMPLEMENTATION_COMPLETE.md`

