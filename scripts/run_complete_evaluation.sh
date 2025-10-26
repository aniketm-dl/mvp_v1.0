#!/bin/bash
################################################################################
# Complete Evaluation Workflow Automation
#
# This script runs the complete evaluation workflow after training completion:
# 1. Automated testing
# 2. Persona assessment
# 3. Version comparison (if previous version exists)
# 4. Sprint report generation
#
# Usage:
#   ./scripts/run_complete_evaluation.sh --version v1.0 --sprint "Sprint 1"
#   ./scripts/run_complete_evaluation.sh --version v2.0 --sprint "Sprint 2" --previous v1.0
#   ./scripts/run_complete_evaluation.sh --version v1.0 --quick  # Quick mode
################################################################################

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
VERSION=""
SPRINT=""
PREVIOUS=""
QUICK=false
OUTPUT_DIR="reports"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --sprint)
            SPRINT="$2"
            shift 2
            ;;
        --previous)
            PREVIOUS="$2"
            shift 2
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --version VERSION --sprint SPRINT [OPTIONS]"
            echo ""
            echo "Required:"
            echo "  --version VERSION    Version to evaluate (e.g., v1.0)"
            echo "  --sprint SPRINT      Sprint name (e.g., 'Sprint 1')"
            echo ""
            echo "Optional:"
            echo "  --previous VERSION   Previous version for comparison"
            echo "  --quick              Quick mode (fewer tests)"
            echo "  --output DIR         Output directory (default: reports)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validation
if [ -z "$VERSION" ]; then
    echo -e "${RED}❌ Error: --version is required${NC}"
    echo "Usage: $0 --version VERSION --sprint SPRINT"
    exit 1
fi

if [ -z "$SPRINT" ]; then
    echo -e "${RED}❌ Error: --sprint is required${NC}"
    echo "Usage: $0 --version VERSION --sprint SPRINT"
    exit 1
fi

# Header
echo "=============================================================================="
echo -e "${CYAN}🎯 COMPLETE PERSONA EVALUATION WORKFLOW${NC}"
echo "=============================================================================="
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  • Version: $VERSION"
echo "  • Sprint: $SPRINT"
if [ -n "$PREVIOUS" ]; then
    echo "  • Previous: $PREVIOUS"
fi
echo "  • Mode: $([ "$QUICK" = true ] && echo "Quick" || echo "Full")"
echo "  • Output: $OUTPUT_DIR"
echo ""

# Check if version exists
if [ ! -d "trained_models/$VERSION" ]; then
    echo -e "${RED}❌ Error: Version $VERSION not found in trained_models/${NC}"
    echo "Available versions:"
    ls -1 trained_models/ | grep -v "latest" | grep -v "README"
    exit 1
fi

START_TIME=$(date +%s)

# Step 1: Automated Testing
echo "=============================================================================="
echo -e "${GREEN}Step 1/4: Running Automated Tests${NC}"
echo "=============================================================================="
echo ""

TEST_ARGS="--version $VERSION --output $OUTPUT_DIR/tests"
if [ "$QUICK" = true ]; then
    TEST_ARGS="$TEST_ARGS --quick"
fi

if python scripts/test_all_personas.py $TEST_ARGS; then
    echo ""
    echo -e "${GREEN}✅ Automated tests passed${NC}"
    TESTS_PASSED=true
else
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed - continuing with evaluation${NC}"
    TESTS_PASSED=false
fi

echo ""
sleep 1

# Step 2: Persona Assessment
echo "=============================================================================="
echo -e "${GREEN}Step 2/4: Running Persona Assessment${NC}"
echo "=============================================================================="
echo ""

ASSESS_ARGS="--version $VERSION --output $OUTPUT_DIR/persona_evaluation"
if [ "$QUICK" = true ]; then
    ASSESS_ARGS="$ASSESS_ARGS --quick"
fi

if python scripts/persona_assessment.py $ASSESS_ARGS; then
    echo ""
    echo -e "${GREEN}✅ Persona assessment completed${NC}"
    ASSESSMENT_PASSED=true
else
    echo ""
    echo -e "${YELLOW}⚠️  Assessment quality gates not met - continuing${NC}"
    ASSESSMENT_PASSED=false
fi

echo ""
sleep 1

# Step 3: Version Comparison (if previous version provided)
if [ -n "$PREVIOUS" ]; then
    echo "=============================================================================="
    echo -e "${GREEN}Step 3/4: Comparing Versions${NC}"
    echo "=============================================================================="
    echo ""
    
    COMPARE_ARGS="$VERSION $PREVIOUS --detailed --output $OUTPUT_DIR/comparisons"
    
    python scripts/compare_persona_versions.py $COMPARE_ARGS
    
    echo ""
    echo -e "${GREEN}✅ Version comparison completed${NC}"
    echo ""
    sleep 1
else
    echo "=============================================================================="
    echo -e "${YELLOW}Step 3/4: Skipping Version Comparison (no previous version)${NC}"
    echo "=============================================================================="
    echo ""
    sleep 1
fi

# Step 4: Sprint Report Generation
echo "=============================================================================="
echo -e "${GREEN}Step 4/4: Generating Sprint Report${NC}"
echo "=============================================================================="
echo ""

REPORT_ARGS="--sprint \"$SPRINT\" --version $VERSION --output $OUTPUT_DIR/sprints"
if [ -n "$PREVIOUS" ]; then
    REPORT_ARGS="$REPORT_ARGS --previous $PREVIOUS"
fi

python scripts/generate_sprint_report.py $REPORT_ARGS

echo ""
echo -e "${GREEN}✅ Sprint report generated${NC}"
echo ""

# Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "=============================================================================="
echo -e "${CYAN}📊 EVALUATION COMPLETE${NC}"
echo "=============================================================================="
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  • Version: $VERSION"
echo "  • Sprint: $SPRINT"

if [ "$TESTS_PASSED" = true ]; then
    echo -e "  • Tests: ${GREEN}✓ PASSED${NC}"
else
    echo -e "  • Tests: ${RED}✗ SOME FAILED${NC}"
fi

if [ "$ASSESSMENT_PASSED" = true ]; then
    echo -e "  • Quality Gates: ${GREEN}✓ PASSED${NC}"
else
    echo -e "  • Quality Gates: ${YELLOW}⚠ NOT MET${NC}"
fi

echo "  • Duration: ${DURATION}s"
echo ""

echo -e "${BLUE}Generated Reports:${NC}"
echo "  • Test Results:    $OUTPUT_DIR/tests/test_report_${VERSION}_*.md"
echo "  • Assessment:      $OUTPUT_DIR/persona_evaluation/${VERSION}_*.md"

if [ -n "$PREVIOUS" ]; then
    echo "  • Comparison:      $OUTPUT_DIR/comparisons/comparison_${VERSION}_vs_${PREVIOUS}_*.md"
fi

SPRINT_FILE=$(echo "$SPRINT" | tr ' ' '_')
echo "  • Sprint Report:   $OUTPUT_DIR/sprints/${SPRINT_FILE}_${VERSION}.html"
echo ""

# Open HTML report if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    HTML_REPORT="$OUTPUT_DIR/sprints/${SPRINT_FILE}_${VERSION}.html"
    if [ -f "$HTML_REPORT" ]; then
        echo -e "${CYAN}🌐 Opening HTML report in browser...${NC}"
        open "$HTML_REPORT"
    fi
fi

echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Review the HTML sprint report (opened in browser)"
echo "  2. Check quality metrics and recommendations"
echo "  3. Compare with previous version (if applicable)"

if [ "$ASSESSMENT_PASSED" = true ] && [ "$TESTS_PASSED" = true ]; then
    echo "  4. ✅ Consider deploying this version to production"
    echo ""
    echo -e "${GREEN}Recommended action: Update latest symlink${NC}"
    echo "  cd trained_models && ln -sf $VERSION latest"
else
    echo "  4. ⚠️  Review failures and make improvements"
    echo ""
    echo -e "${YELLOW}Recommended action: Address issues before deployment${NC}"
fi

echo ""
echo "=============================================================================="

# Exit with appropriate code
if [ "$TESTS_PASSED" = true ] && [ "$ASSESSMENT_PASSED" = true ]; then
    exit 0
else
    exit 1
fi

