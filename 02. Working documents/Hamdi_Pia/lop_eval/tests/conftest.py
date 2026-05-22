import sys
from pathlib import Path

# Hamdi_Pia root (parent of lop_eval)
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
