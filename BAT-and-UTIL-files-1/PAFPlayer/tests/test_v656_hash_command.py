"""V656 command-entry behavior extracted from the active single-file build."""
import ast
from pathlib import Path
import unittest

source=(Path(__file__).resolve().parents[1]/'PAFPlayer.py').read_text(encoding='utf-8')
tree=ast.parse(source)
node=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='PAFHashCommandEntry')
namespace={}
exec(compile(ast.Module(body=[node],type_ignores=[]),'PAFPlayer.py','exec'),namespace)
Entry=namespace['PAFHashCommandEntry']

class HashCommandTests(unittest.TestCase):
    def test_timeout_and_shortcuts(self):
        p=Entry(); self.assertEqual((False,None),p.feed('x',0))
        p.feed('#',0)
        for i,c in enumerate('DJforce'): self.assertEqual((True,None),p.feed(c,(i+1)/10))
        self.assertIsNone(p.expire(2.19)); self.assertEqual('djforce',p.expire(2.2))
        self.assertIsNone(p.expire(3))
    def test_edit_enter_escape(self):
        p=Entry()
        for c in '#djx\b': p.feed(c,0)
        self.assertEqual((True,'dj'),p.feed('\r',.1))
        p.feed('#',1);p.feed('d',1);p.feed('\x1b',1)
        self.assertEqual((False,None),p.feed('j',1))
    def test_expiration_does_not_eat_next_key(self):
        p=Entry()
        for c in '#dj':p.feed(c,0)
        self.assertEqual((False,'dj'),p.feed('x',2))
    def test_empty_and_length(self):
        p=Entry();p.feed('#',0);self.assertIsNone(p.expire(2))
        p.feed('#',3)
        for _ in range(100):p.feed('a',3)
        self.assertEqual(32,len(p.feed('\r',3)[1]))
    def test_both_transport_loops_use_shared_reader(self):
        self.assertIn('action = next_owner_action()',source)
        self.assertIn('paused_action = next_owner_action()',source)
        self.assertIn('command_entry = _HASH_COMMAND_ENTRY',source)

if __name__=='__main__': unittest.main()
