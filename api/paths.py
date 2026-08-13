"""
paths.py

Must be imported before anything that imports from src/ (predict, normalize,
triage_model). src/ has no __init__.py and predict.py does a bare
`from normalize import normalize_message`, so the only correct integration is
inserting src/ onto sys.path -- not a package import.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
