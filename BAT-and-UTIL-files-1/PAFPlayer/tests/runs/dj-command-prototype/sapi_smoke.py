from pathlib import Path
import pythoncom,win32com.client
folder=Path(__file__).resolve().parent/'sapi-smoke'
folder.mkdir(exist_ok=False)
path=folder/'local speech test.wav'
pythoncom.CoInitialize()
try:
 voice=win32com.client.Dispatch('SAPI.SpVoice')
 voices=voice.GetVoices();voice.Voice=voices.Item(0)
 stream=win32com.client.Dispatch('SAPI.SpFileStream')
 stream.Open(str(path),3,False);voice.AudioOutputStream=stream
 voice.Speak('This is a short local speech synthesis test.');stream.Close()
 print('Created local speech WAV:',path,'bytes:',path.stat().st_size)
finally:pythoncom.CoUninitialize()
