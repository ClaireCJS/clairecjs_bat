import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest import mock
import PAFPlayer as p


class PersistenceTests(unittest.TestCase):
    def test_dcc_backup_is_byte_verified_and_reported(self):
        root=Path(tempfile.mkdtemp(prefix='paf456-dcc-'))
        target=root/'PAFPlayer.dcc'; original=b'{"old":"preserve"}'; target.write_bytes(original)
        with mock.patch.object(p,'global_config_developer_choice_available',return_value=True), mock.patch.object(p,'global_config_dcc_path',return_value=target), mock.patch.object(p,'global_config_snapshot',return_value={'test':1}):
            result=p.global_config_save_profile('',developer_choice=True)
        self.assertEqual(str(target.resolve()),result['saved_path'])
        self.assertEqual(original,Path(result['backup_path']).read_bytes())
        self.assertEqual(1,json.loads(target.read_text())['test'])
        self.assertRegex(Path(result['backup_path']).name,r'\.bak\.\d{12}\.replaced-by-chatgpt\.bak$')

    def test_backup_corruption_prevents_overwrite(self):
        root=Path(tempfile.mkdtemp(prefix='paf456-backup-')); target=root/'test.dcc'; target.write_bytes(b'original')
        def corrupt(src,dst): Path(dst).write_bytes(b'corrupt!')
        with mock.patch.object(p.shutil,'copy2',side_effect=corrupt):
            with self.assertRaises(OSError): p._global_config_write_json(target,{'new':1})
        self.assertEqual(b'original',target.read_bytes())

    def test_dcc_prefers_canonical_script(self):
        with mock.patch.object(Path,'is_file',return_value=True):
            self.assertEqual(Path(r'C:\BAT\PAFPlayer.dcc'),p.global_config_dcc_path())
        with mock.patch.object(Path,'is_file',return_value=False):
            self.assertEqual(Path(p.__file__).resolve().with_name('PAFPlayer.dcc'),p.global_config_dcc_path())

    def test_cursor_reset_uses_terminal_default_in_interrupt_cleanup(self):
        stream=mock.Mock(); stream.fileno.return_value=123; stream.isatty.return_value=True
        with mock.patch.object(p.sys,'stdout',stream),mock.patch.object(p.os,'write') as write,mock.patch.object(p,'set_console_cursor_visible'):
            p.restore_terminal_after_interrupt()
        self.assertIn(b'\x1b]112\x07',write.call_args.args[1])


class WebTests(unittest.TestCase):
    def test_complete_javascript_parses(self):
        html=p._paf_web_html(); scripts=re.findall(r'<script[^>]*>(.*?)</script>',html,re.S)
        result=subprocess.run(['node','--check'],input='\n'.join(scripts),text=True,encoding="utf-8",capture_output=True)
        self.assertEqual(0,result.returncode,result.stderr)

    def test_teeny_controls_and_css_keep_solution_out_of_lyric_text(self):
        html=p._paf_web_html()
        self.assertIn('id="teenySize" min="5" max="150" value="20"',html)
        self.assertIn('content:attr(data-solution)',html)
        self.assertIn('webKaraokeSettings.teenySize=Number(e.target.value);saveWebKaraokeSettings()',html)


if __name__=='__main__': unittest.main()
