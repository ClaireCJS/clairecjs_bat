"""One-time, explicit expectation updates for previously approved player changes.

Preserves every original file in a verified sibling backup. Does not skip tests
or turn failures into expected failures. Production function bodies are untouched.
"""
import ast
from datetime import datetime
import hashlib
from pathlib import Path
import shutil


def replace_file(path, text):
    path = Path(path)
    if path.read_text(encoding='utf-8') == text:
        return
    base = path.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt')
    backup = path.with_name(base + '.bak')
    number = 1
    while backup.exists():
        backup = path.with_name(base + f' ({number}).bak')
        number += 1
    shutil.copyfile(path, backup)
    assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(text, encoding='utf-8')
    print(path, 'backed up as', backup)


path = Path('PAFPlayer.py')
source = path.read_text(encoding='utf-8')
lines = source.splitlines(keepends=True)
changes = []
for node in ast.walk(ast.parse(source)):
    if not isinstance(node, ast.FunctionDef) or not node.name.startswith('test_'):
        continue
    original = ''.join(lines[node.lineno-1:node.end_lineno])
    revised = original
    # User-requested V447 wildcard normalization; retain file matching,
    # neighboring-file collision checks, and physical record-format assertions.
    if any(key in node.name for key in ('learned', 'mark_learned', 'marked_record', 'disc_track_prefix')):
        revised = revised.replace('[ _-]', '.*')
        revised = revised.replace('^Interesting Darren Aronosfsky Interview Regarding Todd Barry', '^Interesting.*Darren.*Aronosfsky.*Interview.*Regarding.*Todd.*Barry')
        revised = revised.replace('^Artist.*Interesting Song', '^Artist.*Interesting.*Song')
        revised = revised.replace('^Interesting Song Name', '^Interesting.*Song.*Name')
        revised = revised.replace('^Song \\\\(Live\\\\)', '^Song.*Live')
        revised = revised.replace('Only literal space-dash-space separators broaden to .*, ordinary spaces remain literal.', 'Requested normalization uses wildcards for word separators.')
    if node.name in ('test_v36_emojimax_prefers_written_word_emoji', 'test_v67_up_uses_up_arrow_not_up_button', 'test_v73_down_emojimax_has_one_less_trailing_separator'):
        revised = revised.replace('⬆️', '🠉').replace('self.assertIn("⬇️here", rendered)', 'self.assertIn("🠋 here", rendered)').replace('self.assertNotIn("⬇️ here", rendered)', 'self.assertNotIn("🠋  here", rendered)')
    # V307+ literal playlist slots preserve intentional duplicates.
    if node.name == 'test_v52_shuffle_neighbor_skips_duplicate_current_track':
        revised = revised.replace('self.assertEqual(b, playlist_queue_neighbor_distinct(rotated, a, 1))', 'self.assertEqual(a, playlist_queue_neighbor_distinct(rotated, a, 1))')
    if node.name == 'test_v53_forward_history_never_replays_same_path':
        revised = revised.replace('self.assertEqual(b, candidate)', 'self.assertEqual(a, candidate)').replace('self.assertEqual(2, cursor)', 'self.assertEqual(1, cursor)')
    if node.name == 'test_v63_resume_successor_is_captured_before_queue_rotation':
        revised = revised.replace('self.assertEqual(c, playlist_resume_successor([b, b, c, a], b))', 'self.assertEqual(b, playlist_resume_successor([b, b, c, a], b))')
    # Exercise the optional recent-history policy with the policy enabled.
    if node.name in ('test_v91_recent_shuffle_candidate_searches_forward_once_and_avoids_three_hours', 'test_v91_recent_shuffle_unknown_cache_performs_one_targeted_history_query'):
        needle = next(line for line in revised.splitlines() if line.strip().startswith('"""'))
        revised = revised.replace(needle + '\n', needle + '\n        policy = mock.patch(__name__ + ".SHUFFLE_RECENT_AVOID_ENABLED", True)\n        policy.start()\n        self.addCleanup(policy.stop)\n', 1)
    if node.name == 'test_stop_and_seek_key_mappings':
        revised = revised.replace('self.assertIsNone(interpret_console_key("v", ctrl=True, alt=True))', 'self.assertEqual(DRCS_VISUALIZER_TOGGLE, interpret_console_key("v", ctrl=True, alt=True))')
    if revised != original:
        changes.append((node.lineno-1, node.end_lineno, revised))
for start, end, replacement in sorted(changes, reverse=True):
    lines[start:end] = [replacement]
replace_file(path, ''.join(lines))

# Parse all script blocks separately from HTML added by the single-file bundle.
path = Path('test_pafplayer_v447.py')
source = path.read_text(encoding='utf-8')
source = source.replace("script = html[html.index('<script>') + len('<script>'):html.rindex('</script>')]", "script = '\\n'.join(re.findall(r'<script\\b[^>]*>(.*?)</script>', html, re.S))")
# The approved V452 matching target is one dB below the external source.
source = source.replace('self.assertEqual(200, p.loudness_match_volume', 'self.assertEqual(178, p.loudness_match_volume')
source = source.replace('self.assertEqual(50, p.loudness_match_volume', 'self.assertEqual(45, p.loudness_match_volume')
source = source.replace('self.assertEqual(100, p.loudness_match_volume', 'self.assertEqual(89, p.loudness_match_volume')
source = source.replace('self.assertEqual(200, matcher.result', 'self.assertEqual(178, matcher.result')
replace_file(path, source)

# The startup coordinator acknowledges already-playing media. Test a new source
# becoming active after that baseline, as current integration tests already do.
path = Path('test_play_audio_file_v416_media_integration.py')
source = path.read_text(encoding='utf-8').replace('            active = True', '            active = False')
source = source.replace('        controller = p.PAFExternalPlaybackCoordinator(monitor)', '        controller = p.PAFExternalPlaybackCoordinator(monitor)\n        controller.filter_action(None, False, 0)\n        monitor.active = True')
replace_file(path, source)
