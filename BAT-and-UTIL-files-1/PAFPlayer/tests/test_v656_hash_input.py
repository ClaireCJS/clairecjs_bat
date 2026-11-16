import ast,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
s=(Path(__file__).resolve().parents[1]/'PAFPlayer.py').read_text(encoding='utf8');t=ast.parse(s)
nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('PAFHashCommandEntry','read_windows_key_action')]
nodes[-1].returns=None
for a in nodes[-1].args.args:a.annotation=None
clock=types.SimpleNamespace(now=0.,monotonic=lambda:clock.now)
ns={'os':types.SimpleNamespace(name='nt'),'time':clock};exec(compile(ast.Module(body=nodes,type_ignores=[]),'player','exec'),ns)
ns['_HASH_COMMAND_ENTRY']=ns['PAFHashCommandEntry']();ns['_HASH_COMMAND_PREFIX']='hash-command:';ns['_windows_key_down']=lambda vk:False
class InputLoopTests(unittest.TestCase):
 def test_active_command_uses_nonblocking_input(self):
  chars=list('dj\r');m=types.SimpleNamespace(kbhit=lambda:bool(chars),getwch=lambda:chars.pop(0))
  with patch.dict(sys.modules,{'msvcrt':m}):
   ns['_HASH_COMMAND_ENTRY'].feed('#',0)
   self.assertIsNone(ns['read_windows_key_action']());self.assertIsNone(ns['read_windows_key_action']())
   self.assertEqual('hash-command:dj',ns['read_windows_key_action']())
 def test_timeout_does_not_read_next_key(self):
  chars=['x'];m=types.SimpleNamespace(kbhit=lambda:bool(chars),getwch=lambda:chars.pop(0))
  with patch.dict(sys.modules,{'msvcrt':m}):
   e=ns['_HASH_COMMAND_ENTRY'];e.feed('#',0);e.feed('d',0);e.feed('j',0);clock.now=2
   self.assertEqual('hash-command:dj',ns['read_windows_key_action']());self.assertEqual(['x'],chars)
if __name__=='__main__':unittest.main()
