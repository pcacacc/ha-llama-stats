"""Load HA-independent modules directly so tests run without Home Assistant."""

import importlib.util
import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parent.parent / "custom_components" / "llama_stats"


def _load(name: str):
    module_name = f"llama_stats_{name}"
    spec = importlib.util.spec_from_file_location(module_name, _PKG / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


store = _load("store")
util = _load("util")
