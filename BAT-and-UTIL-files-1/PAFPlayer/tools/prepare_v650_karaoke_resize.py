"""Reduce cold artwork geometry work without changing terminal layout/effects."""
import hashlib
from prepare_v642_artwork_chrome import ROOT,write

path=ROOT/'PAFPlayer.py';source=path.read_text(encoding='utf-8')
assert hashlib.sha256(path.read_bytes()).hexdigest()=='8eb44a53975b44a61838bfa68bd23db00c143dc4451024c86d0f8870ad1c0801'
def change(before,after):
    global source
    assert source.count(before)==1,before[:100]
    source=source.replace(before,after,1)
change("PROGRAM_VERSION                = 'V649'","PROGRAM_VERSION                = 'V650'")
change("PROGRAM_RELEASE_LABEL          = 'V649'","PROGRAM_RELEASE_LABEL          = 'V650'")
change("'2026-11-09-v649-render-blocking'","'2026-11-10-v650-karaoke-resize'")

helper='''def _visualizer_drcs_microtiles_numpy(grid, source_rows, terminal_width, strength_step, mode, layout):
    """Batch the fixed-DRCS scalar quantizer exactly, in bounded 256-cell chunks.

    Pair order, first-distance ties, rounding, foreground luma and downloaded
    glyph selection match _art_detail_quantize_drcs_cached. Other seam strategies
    keep their existing scalar path. No worker, font change or terminal I/O.
    """
    np = _visualizer_numpy()
    if np is None or terminal_width > 4096 or source_rows > 512:
        return None
    vertical = len(grid) // source_rows
    horizontal = min((len(row) for row in grid[:source_rows * vertical]), default=0) // terminal_width
    wanted_horizontal, wanted_vertical = art_detail_geometry(mode)
    if vertical < wanted_vertical or horizontal < wanted_horizontal:
        return None
    try:
        values = np.asarray(grid, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if values.ndim != 3 or values.shape[2] != 3:
        return None
    # Scalar round(float(channel) * factor), including half-to-even rounding.
    values = np.clip(np.rint(values * (strength_step / 1000.0)), 0, 255).astype(np.int32)
    ys = [max(0, min(vertical - 1, round((i + .5) * vertical / wanted_vertical - .5)))
          for i in range(wanted_vertical)]
    xs = [max(0, min(horizontal - 1, round((i + .5) * horizontal / wanted_horizontal - .5)))
          for i in range(wanted_horizontal)]
    y = np.arange(source_rows)[:, None] * vertical + np.asarray(ys)
    x = np.arange(terminal_width)[:, None] * horizontal + np.asarray(xs)
    samples = values[y[:, None, :, None], x[None, :, None, :]].reshape(-1, wanted_horizontal * wanted_vertical, 3)
    bits = samples.shape[1]
    pair_a, pair_b = np.triu_indices(bits, 1)
    weights = 1 << np.arange(bits)
    luma_weights = np.asarray((299, 587, 114))
    output = []
    glyphs = {}
    for start in range(0, len(samples), 256):
        block = samples[start:start + 256]
        delta = block[:, pair_a] - block[:, pair_b]
        best = np.sum(delta * delta, axis=2).argmax(axis=1)
        indexes = np.arange(len(block))
        first, second = block[indexes, pair_a[best]], block[indexes, pair_b[best]]
        fg_delta, bg_delta = block - first[:, None], block - second[:, None]
        assigned = np.sum(fg_delta * fg_delta, axis=2) <= np.sum(bg_delta * bg_delta, axis=2)
        fg_count = assigned.sum(axis=1)
        bg_count = bits - fg_count
        fg = np.rint((block * assigned[:, :, None]).sum(axis=1) / np.maximum(1, fg_count)[:, None]).astype(np.int32)
        bg = np.rint((block * ~assigned[:, :, None]).sum(axis=1) / np.maximum(1, bg_count)[:, None]).astype(np.int32)
        fg[fg_count == 0] = first[fg_count == 0]
        bg[bg_count == 0] = second[bg_count == 0]
        masks = (assigned * weights).sum(axis=1)
        swap = (fg * luma_weights).sum(axis=1) < (bg * luma_weights).sum(axis=1)
        original_fg = fg.copy()
        fg[swap], bg[swap] = bg[swap], original_fg[swap]
        masks[swap] ^= (1 << bits) - 1
        for front, back, mask in zip(fg.tolist(), bg.tolist(), masks.tolist()):
            if mask not in glyphs:
                glyphs[mask] = dense_art_drcs_char(mask, mode, layout)
            glyph, invert = glyphs[mask]
            front, back = tuple(front), tuple(back)
            output.append((back, front, glyph) if invert else (front, back, glyph))
    return tuple(tuple(output[i:i + terminal_width]) for i in range(0, len(output), terminal_width))


'''
change('def _visualizer_art_microtiles(\n',helper+'def _visualizer_art_microtiles(\n')
before='''    scaled = _visualizer_scaled_art_grid(grid, strength, 1)
    if not scaled:
        return tuple()
'''
after='''    # Height changes used to run the Python pairwise quantizer for every cell
    # on the playback thread. Keep identical fixed-DRCS pixels using NumPy.
    if layout_mode and strength_step > 0 and ARTWORK_SEAM_STRATEGY == 5:
        batched = _visualizer_drcs_microtiles_numpy(
            grid, source_rows, terminal_width, strength_step, mode, layout_mode,
        )
        if batched is not None:
            if len(_VISUALIZER_ART_DETAIL_GRID_CACHE) >= 12:
                _VISUALIZER_ART_DETAIL_GRID_CACHE.pop(next(iter(_VISUALIZER_ART_DETAIL_GRID_CACHE)))
            _VISUALIZER_ART_DETAIL_GRID_CACHE[cache_key] = (grid, batched)
            return batched

'''+before
change(before,after)

helper='''_VISUALIZER_ART_VARIANTS_CACHE_LOCK = threading.Lock()
_VISUALIZER_ART_VARIANTS_CACHE = (None, ())
VISUALIZER_ART_VARIANTS_CACHE_MAX_BYTES = 32 * 1024 * 1024


def _visualizer_album_art_variants(audio_path: Path) -> tuple[bytes, ...]:
    """Reuse one bounded source across the compact/expanded artwork layouts.

    The grid LRU already owns geometry-specific results. Keep only this track's
    encoded input, so entering a lyric gap does not reread/fingerprint all covers.
    File/directory signature changes invalidate it; expensive work is outside
    the lock and concurrent extraction still uses the existing single-flight.
    """
    global _VISUALIZER_ART_VARIANTS_CACHE
    key = _album_art_variants_flight_key(audio_path, 4)
    try:
        key += (audio_path.parent.stat().st_mtime_ns,)
    except OSError:
        key += (0,)
    with _VISUALIZER_ART_VARIANTS_CACHE_LOCK:
        if _VISUALIZER_ART_VARIANTS_CACHE[0] == key:
            return _VISUALIZER_ART_VARIANTS_CACHE[1]
    variants = tuple(extract_album_art_variants(audio_path, 4))
    # Extraction can materialize a missing sidecar. Use the resulting signature.
    try:
        key = _album_art_variants_flight_key(audio_path, 4) + (audio_path.parent.stat().st_mtime_ns,)
    except OSError:
        pass
    with _VISUALIZER_ART_VARIANTS_CACHE_LOCK:
        _VISUALIZER_ART_VARIANTS_CACHE = ((key, variants)
            if sum(map(len, variants)) <= VISUALIZER_ART_VARIANTS_CACHE_MAX_BYTES else (None, ()))
    return variants


'''
change('@lru_cache(maxsize=24)\ndef album_art_visualizer_color_grid(',helper+'@lru_cache(maxsize=24)\ndef album_art_visualizer_color_grid(')
change('        variants = extract_album_art_variants(Path(audio_name), 4)','        variants = _visualizer_album_art_variants(Path(audio_name))')
change('self.assertIn(\'extract_album_art_variants(Path(audio_name), 4)\', art_source)',
       'self.assertIn(\'_visualizer_album_art_variants(Path(audio_name))\', art_source)')
compile(source,str(path),'exec')
write('PAFPlayer.py',source)
