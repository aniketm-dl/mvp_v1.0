"""
Smoke test for separation evaluation script.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

def test_separation_script_runs():
    """Separation script should execute without errors"""
    script_path = Path("scripts/eval_separation.py")
    assert script_path.exists(), "Separation script not found"

    # Run script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Should complete (may pass or fail gates, but should not crash)
    assert result.returncode in (0, 1), f"Script crashed with code {result.returncode}: {result.stderr}"

    # Should print metrics
    assert "Silhouette Score:" in result.stdout, "Missing silhouette output"
    assert "Mean Pairwise JSD:" in result.stdout, "Missing JSD output"
    assert "Adjusted Rand Index:" in result.stdout, "Missing ARI output"
