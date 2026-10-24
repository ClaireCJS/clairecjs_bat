"""Compatibility entry point for the old C:\\BAT\\audit_music_batch.py command."""
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
project = Path(r"C:\BAT\audit_music_batch")
sys.path.insert(0, str(project))
runpy.run_path(str(project / "audit_music_batch.py"), run_name="__main__")
