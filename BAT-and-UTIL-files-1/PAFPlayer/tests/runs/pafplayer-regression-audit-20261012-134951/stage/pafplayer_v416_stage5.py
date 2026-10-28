from pafplayer_v416_edit import edit, sub

def update(s):
    i=s.index('ART_COLOR_VISUALIZER_REPRESENTATION = "none"')
    s=s[:i]+'''ARTWORK_SEAM_STRATEGY = 0
ARTWORK_SEAM_STRATEGY_NAMES = (
    "0 — None", "1 — Full-cell glyphs, one-column overlap",
    "2 — Fill isolated one-cell vertical gaps", "3 — Prefer SIXEL bitmap layer",
    "4 — Aspect-aware Chafa symbols", "5 — Avoid mixed DRCS/Unicode artwork",
)

'''+s[i:]
    s=sub(s,'    "ArtColorKaraoke": 0,','    "ArtColorKaraoke": 0,\n    "ArtworkSeamStrategy": 0,')
    s=sub(s,'        "art_color_representation": (0, len(ART_COLOR_VISUALIZER_REPRESENTATIONS) - 1),','        "artwork_seam_strategy": (0, 5),\n        "art_color_representation": (0, len(ART_COLOR_VISUALIZER_REPRESENTATIONS) - 1),')
    s=sub(s,'        "sliders": [','''        "sliders": [''')
    s=sub(s,'    for collection in (schema["selects"], schema["sliders"], schema["toggles"]):','''    schema["selects"].append({"key": "artwork_seam_strategy", "label": "Artwork seam experiment",
        "options": options(ARTWORK_SEAM_STRATEGY_NAMES, start=0), "experimental": True,
        "tooltip": "Experimental / broken: compare painted glyph bounds, cell aspect and mixed charset advances. 0 is unchanged output. SIXEL requires terminal support; gap filling can remove real dark detail."})
    for collection in (schema["selects"], schema["sliders"], schema["toggles"]):''')
    s=sub(s,'  <div class="toggle-grid" id="experimentalControls"></div>','  <div class="toggle-grid" id="experimentalControls"></div>\n  <div class="control-grid" id="artworkSeamControls"></div>')
    s=sub(s,'    else if(item.experimental) host=experimentalSelects;','    else if(item.key===\'artwork_seam_strategy\') host=document.getElementById(\'artworkSeamControls\');\n    else if(item.experimental) host=experimentalSelects;')
    s=sub(s,'            "ProgressStyle": progress_style,','            "ArtworkSeamStrategy": ARTWORK_SEAM_STRATEGY,\n            "ProgressStyle": progress_style,')
    s=sub(s,'    def apply_mode_settings(settings: dict[str, int]) -> None:\n','    def apply_mode_settings(settings: dict[str, int]) -> None:\n        global ARTWORK_SEAM_STRATEGY\n        ARTWORK_SEAM_STRATEGY = max(0, min(5, int(settings.get("ArtworkSeamStrategy", ARTWORK_SEAM_STRATEGY))))\n')
    # Settings are stored/restored using the ordinary player schema.
    s=sub(s,'        global ART_COLOR_VISUALIZER_BAR_OPACITY\n','        global ART_COLOR_VISUALIZER_BAR_OPACITY, ARTWORK_SEAM_STRATEGY\n')
    s=sub(s,'        elif key == "art_color_representation":','''        elif key == "artwork_seam_strategy":
            ARTWORK_SEAM_STRATEGY = max(0, min(5, value))
            _VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
            _VISUALIZER_ART_CELL_STYLE_CACHE.clear()
            last_visualizer_payload = last_visualizer_rows = last_visualizer_cells = None
            last_drcs_position = None
        elif key == "art_color_representation":''')
    s=sub(s,'    global ART_COLOR_VISUALIZER_BAR_OPACITY\n','    global ART_COLOR_VISUALIZER_BAR_OPACITY, ARTWORK_SEAM_STRATEGY\n    ARTWORK_SEAM_STRATEGY = max(0, min(5, int(persisted_settings.get("ArtworkSeamStrategy", 0))))\n')
    s=s.replace('                        art_color_demo=ART_COLOR_VISUALIZER_DEMO_SAVED is not None,','                        artwork_seam_strategy=ARTWORK_SEAM_STRATEGY,\n                        art_color_demo=ART_COLOR_VISUALIZER_DEMO_SAVED is not None,')
    # Main session snapshot preserves this setting across track transitions.
    s=sub(s,"                'ArtColorRepresentation': ART_COLOR_VISUALIZER_REPRESENTATIONS.index(ART_COLOR_VISUALIZER_REPRESENTATION),","                'ArtworkSeamStrategy': ARTWORK_SEAM_STRATEGY,\n                'ArtColorRepresentation': ART_COLOR_VISUALIZER_REPRESENTATIONS.index(ART_COLOR_VISUALIZER_REPRESENTATION),")
    # Modes 1/4 always generate Unicode. Mode 5 chooses exactly one charset.
    s=sub(s,'    if not art_detail_uses_unicode_glyphs(mode) or not glyph:', '    if ARTWORK_SEAM_STRATEGY in {1, 4} and glyph:\n        return True\n    if not art_detail_uses_unicode_glyphs(mode) or not glyph:')
    s=sub(s,'cache_key = (id(grid), int(source_rows), int(terminal_width), strength_step, mode, layout_mode)', 'cache_key = (id(grid), int(source_rows), int(terminal_width), strength_step, mode, layout_mode, ARTWORK_SEAM_STRATEGY)')
    s=sub(s,'    output = []\n    for row in range(source_rows):','''    chafa_cells = chafa_symbol_art_cells(scaled, terminal_width, source_rows) if ARTWORK_SEAM_STRATEGY == 4 else ()
    output = []
    for row in range(source_rows):''')
    s=sub(s,'            if art_detail_is_seamless_adaptive(mode):\n                cells.append','''            if chafa_cells:
                cells.append(chafa_cells[row][column])
            elif ARTWORK_SEAM_STRATEGY == 1:
                color = tuple(round(sum(rgb[c] for rgb in samples) / len(samples)) for c in range(3))
                glyph = "██\\033[1D" if column + 1 < terminal_width else "█"
                cells.append((color, color, glyph))
            elif ARTWORK_SEAM_STRATEGY == 5:
                # Native half blocks only if no DRCS bank is loaded; otherwise
                # quantize every artwork cell into the same downloaded bank.
                if layout_mode:
                    cells.append(_art_detail_quantize_drcs_cached(mode, layout_mode, flattened))
                else:
                    cells.append(_art_detail_quantize_cached(min(3, art_detail_base_mode(mode)), flattened))
            elif art_detail_is_seamless_adaptive(mode):
                cells.append''')
    s=sub(s,'    result = tuple(output)\n    if len(_VISUALIZER_ART_DETAIL_GRID_CACHE)', '    result = fill_artwork_vertical_gaps(tuple(output)) if ARTWORK_SEAM_STRATEGY == 2 else tuple(output)\n    if len(_VISUALIZER_ART_DETAIL_GRID_CACHE)')
    # Bitmap preference uses the already-existing retained SIXEL layering path;
    # this changes no saved SIXEL toggle and falls back when Chafa is absent.
    s=s.replace('not album_art_visualizer_enabled or layered_art_visualizer_enabled or not track_artwork_allowed','not album_art_visualizer_enabled or layered_art_visualizer_enabled or ARTWORK_SEAM_STRATEGY == 3 or not track_artwork_allowed')
    s=s.replace('and layered_art_visualizer_enabled and visualizer_track_artwork_allowed','and (layered_art_visualizer_enabled or (ARTWORK_SEAM_STRATEGY == 3 and shutil.which("chafa"))) and visualizer_track_artwork_allowed')
    i=s.index('_VISUALIZER_ART_DETAIL_GRID_CACHE:')
    s=s[:i]+'''def fill_artwork_vertical_gaps(rows):
    """Experimental: fill only isolated dark cells between bright neighbors.

    Glyph overhang itself is font-dependent; this addresses quantized one-cell
    dark dividers, and can also remove real dark detail. Never enabled by default.
    """
    result = []
    for row in rows:
        cells = list(row)
        for column in range(1, len(row) - 1):
            left, here, right = row[column - 1:column + 2]
            luminance = lambda cell: max(sum(cell[0]), sum(cell[1])) / 3
            if luminance(here) <= 8 and min(luminance(left), luminance(right)) >= 40:
                color = tuple(round((left[0][c] + right[0][c]) / 2) for c in range(3))
                # A space painted with a solid background uses no font bounds.
                cells[column] = (color, color, " ")
        result.append(tuple(cells))
    return tuple(result)


def chafa_symbol_art_cells(grid, columns, rows):
    """Render a cached artwork grid with measured cell aspect and parse its cells."""
    chafa = shutil.which("chafa")
    if not chafa or not grid:
        return ()
    try:
        from PIL import Image
        cw, ch = terminal_cell_pixel_size_nonintrusive()
        image = Image.new("RGB", (len(grid[0]), len(grid)))
        image.putdata([rgb for row in grid for rgb in row])
        image = image.resize((columns * cw, rows * ch))
        stream = io.BytesIO(); image.save(stream, format="PNG")
        process = subprocess.run([chafa, "--format=symbols", "--colors=full",
            "--symbols=half+solid+space", "--optimize=0", "--relative=off", "--probe=off",
            "--animate=off", "--threads=1", "--work=3", "--scale=max",
            f"--font-ratio={cw}/{ch}", f"--size={columns}x{rows}", "-"],
            input=stream.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=3.0, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if process.returncode:
            return ()
        output = []; fg = (255, 255, 255); bg = (0, 0, 0)
        for line in process.stdout.decode("utf-8", errors="replace").splitlines()[:rows]:
            cells = []; index = 0
            while index < len(line):
                ansi = ANSI_CSI_RE.match(line, index)
                if ansi:
                    token = ansi.group(0)
                    if token.endswith("m"):
                        codes = [int(n or 0) for n in token[2:-1].split(";")]
                        j = 0
                        while j < len(codes):
                            code = codes[j]
                            if code in (38, 48) and j + 4 < len(codes) and codes[j + 1] == 2:
                                rgb = tuple(codes[j + 2:j + 5])
                                if code == 38: fg = rgb
                                else: bg = rgb
                                j += 5; continue
                            if code in (0, 39): fg = (255, 255, 255)
                            if code in (0, 49): bg = (0, 0, 0)
                            j += 1
                    index = ansi.end(); continue
                glyph = line[index]; index += 1
                if glyph in " ▀▄▌▐█" and len(cells) < columns:
                    cells.append((fg, bg, glyph))
            cells.extend([((0, 0, 0), (0, 0, 0), " ")] * (columns - len(cells)))
            output.append(tuple(cells))
        if len(output) != rows:
            return ()
        return tuple(output)
    except (ImportError, OSError, ValueError, subprocess.TimeoutExpired):
        return ()


'''+s[i:]
    return s

edit(update)
