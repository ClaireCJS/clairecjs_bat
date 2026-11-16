"""Add on-demand, local-only, bounded thread locations; no background sampler."""
import hashlib
from prepare_v642_artwork_chrome import ROOT, write

path=ROOT/'PAFPlayer.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='df8d90d57b353b976df7e7cff4a88b2f256efc4b43b880214120aa442c1aa6a8'
source=path.read_text(encoding='utf-8')
def change(before,after):
    global source
    assert source.count(before)==1,before[:100]
    source=source.replace(before,after,1)
change("PROGRAM_VERSION                = 'V647'","PROGRAM_VERSION                = 'V648'")
change("PROGRAM_RELEASE_LABEL          = 'V647'","PROGRAM_RELEASE_LABEL          = 'V648'")
change("'2026-11-09-v647-status-publication-stalls'","'2026-11-09-v648-local-stack-diagnostics'")
change('''                if path == "/api/runtime-diagnostics":
                    self._json(200, paf_runtime_diagnostics_snapshot())
                    return''','''                if path == "/api/runtime-diagnostics":
                    from urllib.parse import parse_qs
                    include_stacks = "1" in parse_qs(query).get("stacks", [])
                    if include_stacks and not self._client_is_local():
                        self._json(403, {"error": "Thread locations are available only on the player computer"})
                        return
                    self._json(200, paf_runtime_diagnostics_snapshot(include_stacks=include_stacks))
                    return''')
change('''def paf_runtime_diagnostics_snapshot() -> dict[str, object]:''','''def paf_runtime_thread_stacks() -> list[dict[str, object]]:
    """On-demand locations only: no locals, source reads, heap walks or retained frames."""
    names = {thread.ident: thread.name for thread in threading.enumerate()}
    main_ident = threading.main_thread().ident
    frames = sys._current_frames()
    result = []
    frame = None
    try:
        # Always include the playback/main thread, even with many HTTP clients.
        for ident in sorted(frames, key=lambda key: key != main_ident)[:64]:
            frame = frames[ident]
            stack = []
            for _ in range(32):
                if frame is None:
                    break
                stack.append({"file": os.path.basename(frame.f_code.co_filename)[-192:],
                              "function": frame.f_code.co_name[:192],
                              "line": frame.f_lineno})
                frame = frame.f_back
            result.append({"name": str(names.get(ident, "unknown"))[:128],
                           "main": ident == main_ident, "stack": stack})
        return result
    finally:
        # The snapshot includes this function's own frame. Break that cycle now.
        frame = None
        frames.clear()


def paf_runtime_diagnostics_snapshot(*, include_stacks: bool = False) -> dict[str, object]:''')
change('''        "gc_collections": gc.get_stats(),
    }


def external_presentation_state''','''        "gc_collections": gc.get_stats(),
        **({"thread_stacks": paf_runtime_thread_stacks()} if include_stacks else {}),
    }


def external_presentation_state''')
compile(source,str(path),'exec')
write('PAFPlayer.py',source)
