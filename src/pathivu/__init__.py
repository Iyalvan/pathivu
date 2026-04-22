"""pathivu — record immutable git and build intel into your python artifacts.

'pathivu' (Tamil: பதிவு) means 'record' or 'entry' — a permanent log of what
an artifact is, inscribed into the artifact itself at build time.
"""

from importlib.metadata import PackageNotFoundError, version

from pathivu.core import describe, export_intel
from pathivu.read import read_about

try:
    __version__ = version("pathivu")
except PackageNotFoundError:
    # not installed (e.g. running from a source checkout without pip install -e)
    __version__ = "0.0.0+unknown"

__all__ = ["describe", "export_intel", "read_about", "__version__"]
