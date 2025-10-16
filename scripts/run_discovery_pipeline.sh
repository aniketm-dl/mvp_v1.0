#!/bin/bash
set -e

# Discovery Pipeline Runner - Phase 3E.3
# Runs complete discovery pipeline from embeddings to report

echo "=== Discovery Pipeline - Phase 3E.3 ==="
echo ""

# Configuration
EMB_PATH="${EMB_PATH:-artifacts/encoder/embeddings.parquet}"
CONFIG="${CONFIG:-CONFIGS/discovery.yaml}"
OUT_DIR="${OUT_DIR:-artifacts/discovery}"

# Create output directory
mkdir -p "${OUT_DIR}"

echo "Configuration:"
echo "  Embeddings: ${EMB_PATH}"
echo "  Config: ${CONFIG}"
echo "  Output: ${OUT_DIR}"
echo ""

# Check if embeddings exist
if [ ! -f "${EMB_PATH}" ]; then
    echo "❌ Embeddings not found at ${EMB_PATH}"
    echo "Run: python scripts/export_embeddings.py first"
    exit 1
fi

# Step 1: Build k-NN Graph
echo "[1/6] Building k-NN graph..."
PYTHONPATH=. python discovery/build_graph.py \
    --emb "${EMB_PATH}" \
    --config "${CONFIG}" \
    --out "${OUT_DIR}/graph.pkl"
echo "✓ Graph saved to ${OUT_DIR}/graph.pkl"
echo ""

# Step 2: Clustering
echo "[2/6] Running clustering (HDBSCAN with Leiden fallback)..."
PYTHONPATH=. python discovery/cluster_hdbscan.py \
    --graph "${OUT_DIR}/graph.pkl" \
    --config "${CONFIG}" \
    --out "${OUT_DIR}/labels.pkl"
echo "✓ Labels saved to ${OUT_DIR}/labels.pkl"
echo ""

# Step 3: Bootstrap Stability
echo "[3/6] Running bootstrap stability analysis (20 iterations)..."
PYTHONPATH=. python discovery/stability_bootstrap.py \
    --emb "${EMB_PATH}" \
    --graph "${OUT_DIR}/graph.pkl" \
    --labels "${OUT_DIR}/labels.pkl" \
    --config "${CONFIG}" \
    --out "${OUT_DIR}/stability.pkl"
echo "✓ Stability results saved to ${OUT_DIR}/stability.pkl"
echo ""

# Step 4: Persona Classifier
echo "[4/6] Training persona classifier..."
PYTHONPATH=. python discovery/persona_classifier.py \
    --emb "${EMB_PATH}" \
    --config "${CONFIG}" \
    --out "${OUT_DIR}/persona_classifier.pkl"
echo "✓ Classifier saved to ${OUT_DIR}/persona_classifier.pkl"
echo ""

# Step 5: Generate Report
echo "[5/6] Generating discovery report..."
PYTHONPATH=. python discovery/report.py \
    --emb "${EMB_PATH}" \
    --graph "${OUT_DIR}/graph.pkl" \
    --labels "${OUT_DIR}/labels.pkl" \
    --stability "${OUT_DIR}/stability.pkl" \
    --classifier "${OUT_DIR}/persona_classifier.pkl" \
    --config "${CONFIG}" \
    --out "${OUT_DIR}/report.md"
echo "✓ Report saved to ${OUT_DIR}/report.md"
echo ""

# Step 6: Check Quality Gates
echo "[6/6] Checking quality gates..."
if grep -q "✓ ALL GATES PASSED" "${OUT_DIR}/report.md"; then
    echo "✓ All quality gates passed!"
    echo ""
    echo "Next steps:"
    echo "  1. Review report: cat ${OUT_DIR}/report.md"
    echo "  2. Enable router feature flag: use_encoder_embeddings: true"
    echo "  3. Restart router service"
    echo "  4. Monitor latency and twin assignments"
elif grep -q "✗ SOME GATES FAILED" "${OUT_DIR}/report.md"; then
    echo "⚠ Some quality gates failed"
    echo ""
    echo "Review report for recommendations: cat ${OUT_DIR}/report.md"
    echo ""
    exit 1
else
    echo "⚠ Could not determine gate status"
    echo "Review report manually: cat ${OUT_DIR}/report.md"
    echo ""
fi

echo "=== Discovery Pipeline Complete ==="
