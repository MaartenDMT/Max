# Ensure repository root is on sys.path for tests running under different launchers
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Surface SQLAlchemy 2.0 deprecation warnings during tests
os.environ.setdefault("SQLALCHEMY_WARN_20", "1")

# Suppress noisy Colorama atexit ValueError when streams are closed
try:
    import atexit

    import colorama.initialise as _cinit

    # Capture the originally registered function (if any)
    _orig_reset_all = getattr(_cinit, "reset_all", None)

    def _safe_reset_all() -> None:
        """Best-effort reset that tolerates closed/redirected streams at exit."""
        try:
            stream = getattr(sys, "stdout", None)
            # Use a guard in case colorama internals change
            if hasattr(_cinit, "AnsiToWin32"):
                _cinit.AnsiToWin32(stream).reset_all()
        except Exception:
            # Ignore shutdown-time errors
            return

    # Replace attribute for any direct calls
    _cinit.reset_all = _safe_reset_all  # type: ignore[attr-defined]

    # Unregister the original atexit callback (registered by colorama on import)
    if _orig_reset_all is not None:
        try:
            atexit.unregister(_orig_reset_all)
        except Exception:
            # If not registered or unregister fails, continue
            pass

    # Register our safe version instead
    atexit.register(_safe_reset_all)
except Exception:
    # If anything goes wrong here, do not block tests
    pass
    pass
