import importlib.util
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('v665_bundle_check', root / 'PAFPlayer.py')
player = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = player
spec.loader.exec_module(player)
for name, source in player._PAF_BUNDLED_SOURCES.items():
    compile(source, name, 'exec')
    path = root / 'src' / (name + '.py')
    if path.exists():
        assert path.read_text(encoding='utf8') == source, name
print(f'{len(player._PAF_BUNDLED_SOURCES)} bundles compiled and checked for source parity.')
