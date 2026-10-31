"""Load a chapter's `bin_day.py` by its path, so several chapters can be tested together."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load(path: Path) -> ModuleType:
    """Import the file at `path` under a name unique to its chapter, and return it."""
    path = Path(path).resolve()
    name = f"{path.parent.parent.name}_{path.parent.name}_{path.stem}".replace("-", "_")
    if name in sys.modules:
        return sys.modules[name]
    sys.path.insert(0, str(path.parent))  # for a chapter's own helpers, such as council.py
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module
