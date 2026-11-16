import ast
from pathlib import Path
root=Path(__file__).resolve().parents[3]
tree=ast.parse((root/'PAFPlayer.py').read_text(encoding='utf8')); modules={}
for node in tree.body:
    if not isinstance(node,ast.Assign): continue
    for target in node.targets:
        if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES': modules.update(ast.literal_eval(node.value))
        elif isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES': modules[ast.literal_eval(target.slice)]=ast.literal_eval(node.value)
for name,data in modules.items():
    matches=[x for x in [root/'src'/f'{name}.py',root/'lockscreen'/'src'/f'{name}.py',root/'screensaver'/'src'/f'{name}.py',root/'lockscreen'/f'{name.removeprefix("PAFPlayer_")}.py'] if x.is_file()]
    if len(matches)!=1 or matches[0].read_text(encoding='utf8')!=data: print('Mismatch:',name, matches)
print('Checked',len(modules),'bundles')
