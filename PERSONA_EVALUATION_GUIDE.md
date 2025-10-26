# 🎯 Persona Evaluation & Assessment Guide

## 📋 Overview

This comprehensive guide covers the complete persona evaluation and assessment system for tracking quality improvements across development sprints.

## 🛠️ Tools & Scripts

### 1. **Persona Assessment** (`scripts/persona_assessment.py`)

Evaluates trained persona models across multiple quality dimensions.

```bash
# Evaluate latest version
python scripts/persona_assessment.py

# Evaluate specific version
python scripts/persona_assessment.py --version v1.0

# Quick evaluation (3 personas only)
python scripts/persona_assessment.py --quick

# Detailed output with specific directory
python scripts/persona_assessment.py --version v1.0 --output reports/assessment/
```

**What it evaluates:**
- ✅ Persona consistency (trait alignment, value adherence)
- ✅ Response quality (coherence, relevance, naturalness)
- ✅ Persona differentiation (how distinct personas are)
- ✅ Multi-turn coherence (conversation continuity)
- ✅ Domain expertise (shopping knowledge)

**Outputs:**
- JSON report: `reports/persona_evaluation/{version}_{timestamp}.json`
- Markdown report: `reports/persona_evaluation/{version}_{timestamp}.md`
- Exit code: 0 if quality gates passed, 1 if failed

---

### 2. **Version Comparison** (`scripts/compare_persona_versions.py`)

Compares two model versions to track improvements and regressions.

```bash
# Compare two versions
python scripts/compare_persona_versions.py v1.0 v2.0

# Detailed per-persona comparison
python scripts/compare_persona_versions.py v1.0 v2.0 --detailed

# Generate comparison report
python scripts/compare_persona_versions.py v1.0 v2.0 --detailed --output reports/comparisons/

# Show performance trends across all versions
python scripts/compare_persona_versions.py --trend-analysis
```

**What it shows:**
- ✅ Metric changes (improvements & regressions)
- ✅ Per-persona score changes
- ✅ Deployment recommendation
- ✅ Statistical significance
- ✅ Historical trends

**Outputs:**
- Markdown report: `reports/comparisons/comparison_{v1}_vs_{v2}_{timestamp}.md`
- JSON data: `reports/comparisons/comparison_{v1}_vs_{v2}_{timestamp}.json`

---

### 3. **Sprint Review Reports** (`scripts/generate_sprint_report.py`)

Generates comprehensive sprint review reports after each development cycle.

```bash
# Generate sprint report
python scripts/generate_sprint_report.py --sprint "Sprint 1" --version v1.0

# With comparison to previous sprint
python scripts/generate_sprint_report.py \
    --sprint "Sprint 2" \
    --version v2.0 \
    --previous v1.0

# Custom output directory
python scripts/generate_sprint_report.py \
    --sprint "Sprint 1" \
    --version v1.0 \
    --output reports/sprints/
```

**What it includes:**
- ✅ Sprint goals & achievements
- ✅ Quality metrics & changes
- ✅ Per-persona performance
- ✅ Improvements & regressions
- ✅ Next sprint recommendations
- ✅ Training details

**Outputs:**
- JSON report: `reports/sprints/Sprint_1_v1.0.json`
- Markdown report: `reports/sprints/Sprint_1_v1.0.md`
- HTML report: `reports/sprints/Sprint_1_v1.0.html` (viewable in browser)

---

### 4. **Automated Testing Suite** (`scripts/test_all_personas.py`)

Systematically tests all personas against predefined test scenarios.

```bash
# Test all personas
python scripts/test_all_personas.py

# Test specific version
python scripts/test_all_personas.py --version v1.0

# Quick smoke test (3 personas)
python scripts/test_all_personas.py --quick

# Test specific personas
python scripts/test_all_personas.py --personas bargain_hunter premium_loyalist
```

**What it tests:**
- ✅ Adapter files exist
- ✅ Configuration is valid
- ✅ Model can load
- ✅ Characteristics are well-defined
- ✅ Response generation works

**Outputs:**
- JSON report: `reports/tests/test_report_{version}_{timestamp}.json`
- Markdown summary: `reports/tests/test_report_{version}_{timestamp}.md`
- Exit code: 0 if ≥80% pass rate, 1 otherwise

---

## 📊 Metrics Configuration

All metrics are defined in `CONFIGS/persona_evaluation_metrics.yaml`:

### Core Quality Metrics

1. **Persona Consistency** (weight: 0.25)
   - Trait alignment with OCEAN scores
   - Value adherence (shopping values)
   - Behavior consistency
   - Constraint compliance

2. **Response Quality** (weight: 0.25)
   - Coherence & logical flow
   - Relevance to query
   - Naturalness (human-like)
   - Helpfulness & actionability

3. **Persona Differentiation** (weight: 0.20)
   - Response diversity across personas
   - Decision variance
   - Vocabulary uniqueness
   - Style distinction

4. **Domain Expertise** (weight: 0.15)
   - Product knowledge
   - Shopping strategies
   - Price awareness
   - Trend awareness

5. **Multi-turn Coherence** (weight: 0.15)
   - Context retention
   - Topic continuity
   - Preference memory
   - Contradiction avoidance

### Technical Metrics

- Inference performance (latency, throughput)
- Model efficiency (size, load time)
- Training metrics (convergence, loss)

### Business Metrics

- User satisfaction (simulated)
- Personalization effectiveness
- Recommendation acceptance

---

## 🔄 Complete Workflow

### **Sprint 1: Initial Training**

```bash
# 1. Train models on AWS
./scripts/aws/upload_and_train.sh

# 2. Monitor training (in background)
nohup ./scripts/auto_download_when_ready.sh > auto_download.log 2>&1 &

# 3. Once downloaded, run automated tests
python scripts/test_all_personas.py --version v1.0

# 4. Run comprehensive evaluation
python scripts/persona_assessment.py --version v1.0

# 5. Generate sprint report
python scripts/generate_sprint_report.py --sprint "Sprint 1" --version v1.0

# 6. Review outputs
ls reports/sprints/Sprint_1_v1.0.html  # Open in browser
```

### **Sprint 2: Iterative Improvement**

```bash
# 1. Make improvements based on Sprint 1 recommendations
# (e.g., improve training data, adjust hyperparameters)

# 2. Train new version
./scripts/aws/upload_and_train.sh

# 3. Download and test
python scripts/test_all_personas.py --version v2.0

# 4. Evaluate new version
python scripts/persona_assessment.py --version v2.0

# 5. Compare with previous version
python scripts/compare_persona_versions.py v1.0 v2.0 --detailed --output reports/comparisons/

# 6. Generate sprint report with comparison
python scripts/generate_sprint_report.py \
    --sprint "Sprint 2" \
    --version v2.0 \
    --previous v1.0

# 7. Check for regressions and decide on deployment
# - Review comparison report
# - If recommended, update latest symlink:
ln -sf v2.0 trained_models/latest
```

### **Continuous Monitoring**

```bash
# Show performance trends across all versions
python scripts/compare_persona_versions.py --trend-analysis

# Quick health check
python scripts/test_all_personas.py --quick

# Re-evaluate if models are updated
python scripts/persona_assessment.py --version latest
```

---

## 📈 Quality Gates

Models must pass these quality gates before deployment:

### Minimum Quality
- Overall score ≥ 0.60
- Pass rate ≥ 0.70
- No critical regressions (>10% drop in core metrics)

### Recommended Quality
- Overall score ≥ 0.70
- Pass rate ≥ 0.80
- Persona differentiation ≥ 0.55
- No major regressions (>5% drop)

### Production Ready
- Overall score ≥ 0.80
- Pass rate ≥ 0.90
- All personas individually ≥ 0.70
- Consistent performance across personas

---

## 📁 Directory Structure

```
mvp_v1.0/
├── CONFIGS/
│   └── persona_evaluation_metrics.yaml    # Metrics definitions
│
├── scripts/
│   ├── persona_assessment.py              # Main evaluation script
│   ├── compare_persona_versions.py        # Version comparison
│   ├── generate_sprint_report.py          # Sprint reports
│   └── test_all_personas.py               # Automated testing
│
├── reports/
│   ├── persona_evaluation/                # Assessment results
│   │   ├── v1.0_20241016_143000.json
│   │   └── v1.0_20241016_143000.md
│   │
│   ├── comparisons/                       # Version comparisons
│   │   ├── comparison_v1.0_vs_v2.0.json
│   │   └── comparison_v1.0_vs_v2.0.md
│   │
│   ├── sprints/                           # Sprint reviews
│   │   ├── Sprint_1_v1.0.json
│   │   ├── Sprint_1_v1.0.md
│   │   └── Sprint_1_v1.0.html
│   │
│   └── tests/                             # Test results
│       ├── test_report_v1.0_20241016.json
│       └── test_report_v1.0_20241016.md
│
└── trained_models/
    ├── v1.0/
    ├── v2.0/
    └── latest -> v2.0/
```

---

## 🎯 Best Practices

### 1. **After Each Training Run**
```bash
# Always run tests first
python scripts/test_all_personas.py --version {new_version}

# Then comprehensive evaluation
python scripts/persona_assessment.py --version {new_version}
```

### 2. **Before Deployment**
```bash
# Compare with current production
python scripts/compare_persona_versions.py {current} {new} --detailed

# Check recommendation - deploy only if:
# - ✅ RECOMMENDED or ✓ APPROVED
# - No critical regressions
```

### 3. **End of Sprint**
```bash
# Generate comprehensive sprint report
python scripts/generate_sprint_report.py \
    --sprint "Sprint X" \
    --version {new_version} \
    --previous {old_version}

# Review HTML report for stakeholders
open reports/sprints/Sprint_X_{version}.html
```

### 4. **Version Management**
```bash
# Keep all versions
# NEVER delete old versions - archive instead
mv trained_models/v1.0 trained_models/archive/v1.0

# Update latest only after thorough validation
ln -sf v2.1_lora_improved trained_models/latest
```

---

## 🔍 Interpreting Results

### Assessment Scores

| Score | Meaning | Action |
|-------|---------|--------|
| 0.80+ | Excellent | Ready for production |
| 0.70-0.79 | Good | Minor improvements suggested |
| 0.60-0.69 | Acceptable | Significant improvements needed |
| < 0.60 | Poor | Major rework required |

### Comparison Recommendations

| Recommendation | Meaning | Action |
|---------------|---------|--------|
| ✅ RECOMMENDED | Significant improvements | Deploy immediately |
| ✓ APPROVED | Minor improvements | Safe to deploy |
| = NEUTRAL | No significant changes | Optional deployment |
| ⚠️ REVIEW NEEDED | Some regressions | Review carefully |
| 🚫 DO NOT DEPLOY | Critical regressions | Do not deploy |

### Pass Rates

- **≥80%**: Excellent - All systems go
- **70-79%**: Good - Minor issues
- **60-69%**: Acceptable - Needs attention
- **<60%**: Poor - Major problems

---

## 🆘 Troubleshooting

### No evaluation results found
```bash
# Run evaluation first
python scripts/persona_assessment.py --version v1.0
```

### Version not found
```bash
# List available versions
python scripts/compare_persona_versions.py --trend-analysis

# Check trained_models directory
ls trained_models/
```

### Tests failing
```bash
# Check specific failure details in JSON report
cat reports/tests/test_report_v1.0_latest.json | jq '.persona_suites[] | select(.pass_rate < 0.8)'

# Test specific failing personas
python scripts/test_all_personas.py --personas {failing_persona_id}
```

### Slow evaluation
```bash
# Use quick mode for initial testing
python scripts/persona_assessment.py --quick

# Or specify fewer personas in test_all_personas.py
python scripts/test_all_personas.py --personas bargain_hunter premium_loyalist
```

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review individual tool help: `python scripts/{tool}.py --help`
3. Check metrics config: `CONFIGS/persona_evaluation_metrics.yaml`
4. Review generated reports for detailed diagnostics

---

## 🎉 Quick Start Checklist

After training completion:

- [ ] Run automated tests
- [ ] Run persona assessment
- [ ] Compare with previous version (if exists)
- [ ] Generate sprint report
- [ ] Review HTML report
- [ ] Check quality gates
- [ ] Update latest symlink (if passing)
- [ ] Archive old versions (if needed)

---

**Remember:** Every version is valuable. Always preserve working models and document changes!

