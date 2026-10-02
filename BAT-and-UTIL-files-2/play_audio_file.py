#!/usr/bin/env python3
"""Compatibility entry point; PAFPlayer.py is the single implementation."""
from pathlib import Path as _LegacyPath
_PAF_CANONICAL_PATH = _LegacyPath(__file__).resolve().with_name("PAFPlayer.py")
__file__ = str(_PAF_CANONICAL_PATH)
# Execute in this module's namespace so legacy importers and their patches keep
# referring to the same globals as the functions they call.
exec(compile(_PAF_CANONICAL_PATH.read_bytes(), __file__, "exec"), globals(), globals())