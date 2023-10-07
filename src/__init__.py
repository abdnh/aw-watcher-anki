import sys

if "pytest" not in sys.modules:
    from . import main
