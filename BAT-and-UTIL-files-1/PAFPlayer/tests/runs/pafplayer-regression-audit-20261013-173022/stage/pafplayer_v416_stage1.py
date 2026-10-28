from pafplayer_v416_edit import edit, sub

def update(s):
    s = sub(s, '# CHAT ARTIFACT BUILD: 2026-09-10-V414-PLAY-ORDER-MODES', '# CHAT ARTIFACT BUILD: 2026-09-14-V416-TIMELINE-TODOS-AND-KARAOKE-SPACING')
    s = sub(s, 'PROGRAM_VERSION                 = "V414"', 'PROGRAM_VERSION                 = "V416"')
    marker = '# V369 plural normalization.'
    i = s.index(marker)
    s = s[:i] + '''# V416: final curated removals apply after the imported survey dictionaries.
EMOJIMAX_V416_REMOVED = frozenset({
    "puked", "yelling", "flick", "flicking", "singing", "faced", "face", "faces", "facing",
    "confront", "confronted", "encounter", "encountered", "stare", "stared", "opposite",
    "stuck", "trapped", "jammed", "blocked", "stranded", "stalled", "cream", "single",
    "double", "triple", "quadruple", "quintuple", "sextuple", "septuple", "octuple",
    "nonuple", "decuple", "slice", "broke", "teenage",
})
for _v416_table in (semantic, SEMANTIC_PHRASES):
    for _v416_word in EMOJIMAX_V416_REMOVED:
        _v416_table.pop(_v416_word, None)
    for _v416_word in ("grew", "person", "30", "thirty"):
        _v416_table.pop(_v416_word, None)
semantic.update({"grew": "🌱", "person": "👤", "30": "㉚", "thirty": "㉚"})
# Explicit inflections track their base mapping; do not infer arbitrary verbs.
EMOJIMAX_BASE_SUFFIX = {
    "praying": ("pray", "ing"), "speaking": ("speak", "ing"),
    "talking": ("talk", "ing"), "licking": ("lick", "ing"),
    "worshipping": ("worship", "ping"),
}
for _v416_word in EMOJIMAX_BASE_SUFFIX:
    semantic.pop(_v416_word, None)
    SEMANTIC_PHRASES.pop(_v416_word, None)

''' + s[i:]
    s = sub(s, '    replacement = semantic.get(folded)\n', '''    if folded in EMOJIMAX_V416_REMOVED:
        return None
    if folded in EMOJIMAX_BASE_SUFFIX:
        base, suffix = EMOJIMAX_BASE_SUFFIX[folded]
        replacement = semantic.get(base)
        return str(replacement) + suffix if replacement is not None else None
    replacement = semantic.get(folded)
''')
    s = sub(s, '    for word in text.split():\n        proposal = word if not current else current + " " + word', '''    # Generated Windows Terminal safety cells must survive the current-line
    # wrapping path exactly as they do the previous/next line paths. split()
    # collapsed two safety cells + a source space back to one source space.
    for match in re.finditer(r"(\\s*)(\\S+)", str(text)):
        gap, word = match.groups()
        proposal = word if not current else current + gap + word''')
    s = sub(s, '    return re.sub(r"(?i)^https?://(?:www\\.)?", "", text)', '    return re.sub(r"(?i)^https?://(?:www\\.)?", "", text).rstrip("/")')
    s = sub(s, '``rammstein.com/`` without changing', '``rammstein.com`` without changing')
    s = sub(s, '{web_server.port}  {web_server.url}"', '{web_server.port}  {web_server.url.rstrip(chr(47))}"', count=2)
    s = sub(s, '    if first.casefold() == "x":\n', '''    if not ctrl and not alt and first.casefold() == "j":
        return PLAYLIST_ADD_SEARCH
    if first.casefold() == "x":
''')
    s = s.replace("?'📁🔁':", "?'🔁📁':").replace("?'☷🔁':", "?'🔁☷':")
    # Clear silence before either decay or adaptive motion can invent activity.
    s = sub(s, '    dt = max(0.0, float(delta))\n    detector = min(len(PROGRESS_BEAT_DETECTOR_NAMES)', '''    if not levels or not any(levels):
        state.clear()
        state["pulse"] = 0.0
        return 0.0
    dt = max(0.0, float(delta))
    detector = min(len(PROGRESS_BEAT_DETECTOR_NAMES)''')
    s = sub(s, '        difference = abs(energy - previous_energy)', '        difference = max(0.0, energy - previous_energy)')
    # No stale frame fallback for a song timeline. Live capture stays separate.
    s = sub(s, '(spectrum_frame_interpolated_at(drcs_timeline, current_position) or progress_visualizer_levels)', 'spectrum_frame_interpolated_at(drcs_timeline, current_position)')
    # Reset detector memory at discontinuities, not just its delta.
    s = sub(s, '            beat_delta = 1.0 / max(1, SPECTRUM_ANALYSIS_FPS)\n        else:', '            progress_beat_state.clear()\n            beat_delta = 1.0 / max(1, SPECTRUM_ANALYSIS_FPS)\n        else:')
    return s

edit(update)
