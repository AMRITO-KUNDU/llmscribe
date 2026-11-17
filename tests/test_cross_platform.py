"""The cross-platform check must run, and be stable on one machine."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "cross_platform_check.py"


def run() -> str:
    proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_check_reports_a_combined_digest():
    out = run()
    assert "combined" in out
    for operation in ("map", "overview", "search", "read", "read_many", "dependencies"):
        assert operation in out, f"{operation} missing from the digest report"


def test_check_is_stable_on_this_machine():
    """Same machine, two runs, same digest - otherwise CI comparison is meaningless."""
    first = [line for line in run().splitlines() if line.startswith("combined")][0]
    second = [line for line in run().splitlines() if line.startswith("combined")][0]
    assert first == second
