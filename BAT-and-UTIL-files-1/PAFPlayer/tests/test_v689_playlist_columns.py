import importlib.util,sys,tempfile,unittest,types
from pathlib import Path
from unittest import mock
spec=importlib.util.spec_from_file_location('v689',str(Path(__file__).resolve().parents[1]/'PAFPlayer.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
import PAFPlayer_playlist_window as w
class Tests(unittest.TestCase):
 def test_last_played_and_folder_are_available(self):
  v=w.metadata_extra('test.mp3',lambda path:1600000000);self.assertIn('2020',v['last_played']);self.assertIn('folder',v)
 def test_edit_verifies_backup_and_preserves_other_tags(self):
  folder=Path(tempfile.mkdtemp());path=folder/'song.mp3';path.write_bytes(b'original')
  class Media(dict):
   tags=True
   def save(self):path.write_bytes(b'edited')
  media=Media({'other':['keep']})
  with mock.patch.dict(sys.modules,{'mutagen':types.SimpleNamespace(File=lambda *a,**k:media)}):backup=w.write_audio_tags(path,{'title':'New title','artist':'Band'})
  self.assertEqual(b'original',backup.read_bytes());self.assertEqual(b'edited',path.read_bytes());self.assertEqual(['keep'],media['other']);self.assertEqual(['New title'],media['title'])
 def test_backup_failure_prevents_save(self):
  folder=Path(tempfile.mkdtemp());path=folder/'song.mp3';path.write_bytes(b'original');media=mock.Mock();media.tags=True
  with mock.patch.dict(sys.modules,{'mutagen':types.SimpleNamespace(File=lambda *a,**k:media)}),mock.patch.object(w.shutil,'copyfileobj',side_effect=OSError('no space')):
   with self.assertRaises(OSError):w.write_audio_tags(path,{'title':'New'})
  media.save.assert_not_called();self.assertEqual(b'original',path.read_bytes())
 def test_header_and_tag_selection_are_exposed(self):
  import inspect
  s=inspect.getsource(w.PlaylistWindow._run_tk);self.assertIn("header.bind('<Button-3>',show_column_menu)",s);self.assertIn("root.bind('<Alt-KeyPress-3>',edit_tags)",s);self.assertIn('if len(indexes)!=1',s);self.assertIn("'last_played':('Last played',20)",s)
if __name__=='__main__':unittest.main()
