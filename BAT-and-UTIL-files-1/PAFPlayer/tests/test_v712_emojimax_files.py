import importlib.util,io,sys,tempfile,unittest
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
spec=importlib.util.spec_from_file_location("v712_player",Path(__file__).resolve().parents[1]/"PAFPlayer.py");player=importlib.util.module_from_spec(spec);sys.modules[spec.name]=player;spec.loader.exec_module(player)
class EmojimaxFileTests(unittest.TestCase):
 def setUp(self):self.root=Path(tempfile.mkdtemp(prefix="paf-emojimax-test-"))
 def test_whitespace_original_and_collision(self):
  source=self.root/"words.txt";raw=b"  hello world  \r\n\r\n  moon  \r\n";source.write_bytes(raw)
  with redirect_stdout(io.StringIO()):
   self.assertEqual(0,player.main(["--emojimax",str(source)]));self.assertEqual(0,player.main(["--emojimaxx",str(source)]))
  result=(self.root/"words - Emojimax.txt").read_bytes();self.assertNotEqual(raw,result);self.assertEqual(raw,source.read_bytes());self.assertTrue(result.startswith(b"  "));self.assertTrue(result.endswith(b"  \r\n"));self.assertIn(b"\r\n\r\n",result);self.assertEqual(result,(self.root/"words - Emojimax (1).txt").read_bytes())
 def test_utf16_endianness_and_bom(self):
  source=self.root/"text.txt";raw=b"\xfe\xff"+" hello world \r\n".encode("utf-16-be");source.write_bytes(raw)
  with redirect_stdout(io.StringIO()):self.assertEqual(0,player.main(["--emojimax-file",str(source)]))
  result=(self.root/"text - Emojimax.txt").read_bytes();self.assertTrue(result.startswith(b"\xfe\xff"));self.assertTrue(result[2:].decode("utf-16-be").endswith(" \r\n"));self.assertEqual(raw,source.read_bytes())
 def test_binary_is_not_converted(self):
  source=self.root/"data.bin";source.write_bytes(b"hello\x00world")
  with redirect_stderr(io.StringIO()):self.assertEqual(1,player.main(["--emojimax-file",str(source)]))
  self.assertFalse((self.root/"data - Emojimax.bin").exists())
if __name__=="__main__":unittest.main()
