import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('storage',str(Path(__file__).resolve().parents[1]/'src'/'PAFPlayer_model_storage.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_verified_move_preserves_original(self):
  base=Path(tempfile.mkdtemp());source=base/'source';source.mkdir();(source/'model.bin').write_bytes(b'weights');dest=base/'dest';links=[]
  def fake_link(old,new):links.append((old,new));old.mkdir()
  result=m.relocate(dest,source_list=[('voice',source,'.')],link=fake_link)
  self.assertEqual(b'weights',(dest/'model.bin').read_bytes());self.assertEqual(b'weights',(Path(result[0]['backup'])/'model.bin').read_bytes());self.assertEqual(dest,links[0][1])
 def test_existing_destination_is_preserved(self):
  base=Path(tempfile.mkdtemp());source=base/'source';source.mkdir();(source/'data').write_bytes(b'source');dest=base/'dest';dest.mkdir();(dest/'other').write_bytes(b'keep')
  with self.assertRaises(FileExistsError):m.relocate(dest,source_list=[('voice',source,'.')],link=lambda a,b:None)
  self.assertEqual(b'keep',(dest/'other').read_bytes());self.assertEqual(b'source',(source/'data').read_bytes())
 def test_failed_junction_restores_original(self):
  base=Path(tempfile.mkdtemp());source=base/'source';source.mkdir();(source/'data').write_bytes(b'source');dest=base/'dest'
  def fail(*a):raise OSError('failed')
  with self.assertRaises(OSError):m.relocate(dest,source_list=[('voice',source,'.')],link=fail)
  self.assertEqual(b'source',(source/'data').read_bytes());self.assertEqual(b'source',(dest/'data').read_bytes())
if __name__=='__main__':unittest.main()
