import importlib.util,io,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
spec=importlib.util.spec_from_file_location("dj_collage",str(Path(__file__).resolve().parents[1]/"src"/"PAFPlayer_dj.py"));dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
class Tests(unittest.TestCase):
 def test_all_songs_have_uncropped_tiles_and_no_sidecar_writes(self):
  folder=Path(tempfile.mkdtemp());red=folder/"red.png";blue=folder/"blue.png";Image.new("RGB",(20,10),"red").save(red);Image.new("RGB",(10,20),"blue").save(blue)
  app=SimpleNamespace(_album_art_candidates=lambda path:[red if path.name=="one.mp3" else blue],_folder_uses_per_track_sidecar_art=lambda path:True,_extract_tagged_embedded_cover_art=lambda path:None,_path_has_misc_component=lambda path:True)
  before={x.name:x.read_bytes() for x in folder.iterdir()}
  data=dj.build_dj_collage([{"artist":"A","title":"One","_path":str(folder/"one.mp3")},{"artist":"B","title":"Two","_path":str(folder/"two.mp3")}],app)
  with Image.open(io.BytesIO(data)) as image:
   self.assertEqual((720,360),image.size);self.assertEqual((255,0,0),image.getpixel((180,180)));self.assertEqual((0,0,255),image.getpixel((540,180)))
  self.assertEqual(before,{x.name:x.read_bytes() for x in folder.iterdir()})
if __name__=="__main__":unittest.main()
