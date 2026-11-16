from pathlib import Path
import importlib.util,io,sys,unittest
root=Path(__file__).resolve().parents[3]
names=['test_v174_play_pause_state_persists_and_defaults_to_playing','test_v172_web_pause_is_a_real_toggle_and_spectrum_uses_small_endpoint','test_v247_experimental_web_controls_are_bottom_group']
for label,path in [('V656',root/'releases/PAFPlayer_v656_hash_command_foundation.py'),('V657',root/'PAFPlayer.py')]:
 spec=importlib.util.spec_from_file_location('compare_'+label,path);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
 result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(mod.PlayWaveFileTests(x) for x in names))
 print(label,'ran',result.testsRun,'failures',[str(x).split(' ')[0] for x,_ in result.failures],'errors',[str(x).split(' ')[0] for x,_ in result.errors])
