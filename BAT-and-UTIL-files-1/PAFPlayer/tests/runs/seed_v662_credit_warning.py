"""Record the previously verified credit-balance observation for this key."""
import os,sys
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
import PAFPlayer_dj as dj
config=Path(os.environ['LOCALAPPDATA'])/'PAFPlayer'/'workflows'
warning=dj.CreditWarnings(SimpleNamespace(root=config))
if not warning.key_id:raise SystemExit('No current OpenAI key; warning was not seeded')
warning.set(True)
if not warning.messages():raise SystemExit('Warning state was not set')
print('Stored the previously observed OpenAI credit warning for the current key.')
