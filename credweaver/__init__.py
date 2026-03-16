"""CredWeaver — Weave profile data into targeted credential wordlists."""

__version__ = "2.0.0"
__author__ = "CredWeaver Contributors"
__license__ = "MIT"

from credweaver.core.engine import Engine
from credweaver.core.profile import Profile

__all__ = ["Engine", "Profile", "__version__"]
