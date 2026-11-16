import pyttsx3
from pathlib import Path
folder=Path(__file__).resolve().parent/'pyttsx-smoke'
folder.mkdir(exist_ok=False)
path=folder/'local speech test.wav'
engine=pyttsx3.init('sapi5');engine.save_to_file('This is a short local speech synthesis test.',str(path));engine.runAndWait()
print('Output exists:',path.exists(),'bytes:',path.stat().st_size if path.exists() else 0)
