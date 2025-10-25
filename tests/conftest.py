from pathlib import Path
import sys

# Ensure repo root is on sys.path so imports like
# `from custom_components.voice-replay import const` work during tests.
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
