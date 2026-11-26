"""Application-owned runtime storage; independent of the invoking shell's folder."""
from pathlib import Path


def runtime_root():
    directory = Path(__file__.split('::', 1)[0]).resolve().parent
    if directory.name == 'src': directory = directory.parent
    return directory / 'runtime'


def helper_directory():
    return runtime_root() / 'clairecjs_utils'


def migrate_flat_helpers(appdir=None):
    """Move known legacy downloads under runtime, preserving every collision."""
    directory = Path(appdir).resolve() if appdir is not None else runtime_root().parent
    target = directory / 'runtime' / 'clairecjs_utils'
    moved = []
    for source in sorted(directory.glob('claire_*.py')):
        if not source.is_file(): continue
        target.mkdir(parents=True, exist_ok=True)
        destination = target / source.name
        if destination.exists():
            # Retain the original runtime file and the legacy copy.
            archive = target / 'legacy'; archive.mkdir(exist_ok=True)
            destination = archive / source.name; index = 0
            while destination.exists():
                index += 1; destination = archive / (source.stem + f' ({index})' + source.suffix)
        source.rename(destination)
        moved.append((str(source), str(destination)))
    return moved
