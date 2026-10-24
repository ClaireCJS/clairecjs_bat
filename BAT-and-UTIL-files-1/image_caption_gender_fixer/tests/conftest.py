"""Tests may use local native tools, but must never download/install software."""
import urllib.request
import subprocess
import pytest


@pytest.fixture(autouse=True)
def no_real_installations_or_network(monkeypatch):
    def blocked(*a,**kw):
        raise AssertionError("A test attempted real network access")
    monkeypatch.setattr(urllib.request,"urlopen",blocked)
    original=subprocess.run
    def checked(command,*a,**kw):
        text=" ".join(str(x) for x in command) if not isinstance(command,str) else command
        if any(name in text.lower() for name in ("choco.exe install","choco install","winget install","pip install","pip download")):
            raise AssertionError("A test attempted real dependency installation")
        return original(command,*a,**kw)
    monkeypatch.setattr(subprocess,"run",checked)
