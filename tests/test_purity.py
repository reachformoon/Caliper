import subprocess
import sys
from pathlib import Path


def test_core_purity() -> None:
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_core_purity.py")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
