"""Refresh the existing literal bundle with the reviewed external feature sources."""
import ast
from edit_v568 import ROOT, write

def sync(source):
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines: offsets.append(offsets[-1] + len(line))
    changes = []
    for name in ('PAFPlayer_monkeymote', 'PAFPlayer_workflows_ui', 'PAFPlayer_web_workflows'):
        matches = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                matches.extend(v for k,v in zip(node.keys,node.values) if isinstance(k,ast.Constant) and k.value==name)
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)==name:
                        matches.append(node.value)
        assert len(matches) == 1, (name,len(matches))
        node = matches[0]
        # AST columns are UTF-8 byte offsets, not Python character offsets.
        def position(line, column):
            return offsets[line-1] + len(lines[line-1].encode('utf-8')[:column].decode('utf-8'))
        changes.append((position(node.lineno,node.col_offset),position(node.end_lineno,node.end_col_offset),repr((ROOT/(name+'.py')).read_text(encoding='utf-8'))))
    for start,end,value in sorted(changes,reverse=True): source=source[:start]+value+source[end:]
    return source

if __name__ == '__main__': write('PAFPlayer.py',sync((ROOT/'PAFPlayer.py').read_text(encoding='utf-8')))
