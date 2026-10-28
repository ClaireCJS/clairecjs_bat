"""V519 sparse terminal transport: semantic equivalence, bounds and output savings."""
import ast, ctypes, random, re, sys, unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import PAFPlayer as p


def baseline():
    tree=ast.parse((ROOT/'releases/PAFPlayer_v518_lockscreen_stable_lyrics.py').read_text(encoding='utf-8-sig'))
    ns=dict(vars(p))
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('_PAF_ART_ENCODER_BINARY','_PAF_ART_ENCODER_SHA256') for t in n.targets):
            exec(compile(ast.Module(body=[n],type_ignores=[]),'<baseline>','exec'),ns)
    for name in ('_visualizer_artwork_encoder','_visualizer_packed_art_delta'):
        n=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.Module(body=[n],type_ignores=[]),'<baseline>','exec'),ns)
    return ns['_visualizer_packed_art_delta']


def apply_vt(text, rows):
    """Independent tiny VT interpreter for our encoder's cursor/color/glyph contract."""
    grid=[[list(row[x:x+7]) for x in range(0,len(row),7)] for row in rows]
    y=x=0;fg=bg=None;drcs=False;i=0
    while i<len(text):
        if text.startswith('\x1b[',i):
            m=re.match(r'\x1b\[([?0-9;]*)([A-Za-z])',text[i:]);assert m,text[i:i+30]
            params,code=m.groups();i+=m.end()
            if code=='H':y,x=[int(v)-1 for v in params.split(';')]
            elif code=='G':x=int(params)-1
            elif code=='m':
                if params=='0':fg=bg=None;continue
                values=[int(v) for v in params.split(';')];at=0
                while at<len(values):
                    channel,mode=values[at:at+2];assert mode==2
                    rgb=values[at+2:at+5];assert len(rgb)==3
                    if channel==38:fg=rgb
                    elif channel==48:bg=rgb
                    else:raise AssertionError(channel)
                    at+=5
            else:assert code in ('h','l'),code
        elif text.startswith('\x1b( @',i):drcs=True;i+=4
        elif text.startswith('\x1b(B',i):drcs=False;i+=3
        elif text.startswith('\x1b#5',i):i+=3
        else:
            assert drcs and fg is not None and bg is not None
            assert 0<=y<len(grid) and 0<=x<len(grid[y]),(y,x)
            grid[y][x]=fg+bg+[ord(text[i])];x+=1;i+=1
    assert not drcs
    return [bytes(v for cell in row for v in cell) for row in grid]


class SparseTransport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.old=staticmethod(baseline())
    def origins(self,n):return [f'\x1b[?7l\x1b(B\x1b[{i+1};1H\x1b#5' for i in range(n)]
    def test_full_frame_bytes_unchanged(self):
        rng=random.Random(519)
        for width in (1,12,170):
            rows=[bytes(rng.randrange(256) if j%7<6 else rng.randrange(33,127) for j in range(width*7)) for _ in range(3)]
            self.assertEqual(self.old(rows,None,self.origins(3)),p._visualizer_packed_art_delta(rows,None,self.origins(3)))
    def test_sparse_dense_and_color_channel_changes_keep_every_cell(self):
        rng=random.Random(521)
        self.assertIsNotNone(p._visualizer_artwork_encoder())
        for width in (1,7,37,170,301):
            old=[bytes(rng.randrange(256) if j%7<6 else rng.randrange(33,127) for j in range(width*7)) for _ in range(4)]
            for density in (.01,.1,.5,1.):
                rows=[bytearray(r) for r in old]
                for row in rows:
                    for x in range(width):
                        if rng.random()<density:
                            channel=rng.randrange(7);row[x*7+channel]=rng.randrange(256) if channel<6 else rng.randrange(33,127)
                rows=list(map(bytes,rows));origins=self.origins(4)
                encoded=p._visualizer_packed_art_delta(rows,old,origins)
                with mock.patch.object(p,'_visualizer_artwork_encoder',return_value=None):fallback=p._visualizer_packed_art_delta(rows,old,origins)
                self.assertEqual(fallback,encoded)
                self.assertEqual(rows,apply_vt(encoded[0],old))
                self.assertLessEqual(len(encoded[0]),len(self.old(rows,old,origins)[0]))
                old=rows
    def test_unchanged_frame_is_empty(self):
        rows=[bytes([1,2,3,4,5,6,65])*170]*32
        self.assertEqual(('',0),p._visualizer_packed_art_delta(rows,rows,self.origins(32)))
    def test_distant_changes_do_not_repaint_artwork_between_them(self):
        row=b''.join(bytes([x%256,22,33,44,55,66,65]) for x in range(170))
        old=[row]*32;rows=[]
        for r in old:
            r=bytearray(r);r[6]=66;r[-1]=67;rows.append(bytes(r))
        new=p._visualizer_packed_art_delta(rows,old,self.origins(32))[0]
        original=self.old(rows,old,self.origins(32))[0]
        self.assertLess(len(new),len(original)*.1)
        self.assertEqual(rows,apply_vt(new,old))
    def test_shape_change_forces_complete_frame(self):
        rows=[bytes([1,2,3,4,5,6,65])*12]*3
        self.assertEqual(p._visualizer_packed_art_delta(rows,None,self.origins(3)),p._visualizer_packed_art_delta(rows,[b'bad'],self.origins(3)))
    def test_short_gaps_choose_fewer_bytes(self):
        row=bytes([1,2,3,4,5,6,65])*12;changed=bytearray(row);changed[6]=66;changed[20]=67
        got=p._visualizer_packed_art_delta([bytes(changed)],[row],self.origins(1))
        self.assertEqual(got[1],1)
        self.assertEqual([bytes(changed)],apply_vt(got[0],[row]))
    def test_native_capacity_rejection_does_not_write(self):
        encoder=p._visualizer_artwork_encoder();self.assertIsNotNone(encoder)
        out=ctypes.create_string_buffer(b'unchanged');before=out.raw;runs=ctypes.c_int()
        cur=ctypes.create_string_buffer(bytes([1,2,3,4,5,6,65]));orig=ctypes.create_string_buffer(b'abc');length=(ctypes.c_longlong*1)(3)
        self.assertEqual(-1,encoder(cur,None,orig,length,1,1,3,out,1,ctypes.byref(runs)))
        self.assertEqual(before,out.raw)

if __name__=='__main__':unittest.main()
