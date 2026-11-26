import ast,inspect,math,threading,unittest
from types import SimpleNamespace
from unittest.mock import Mock
import PAFPlayer as app

class IdlePacingTests(unittest.TestCase):
    def extracted(self,name,env):
        tree=ast.parse(inspect.getsource(app.ExternalAlbumArtWindow))
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
        # These callbacks close over the artwork worker's state.
        node.body=[n for n in node.body if not isinstance(n,ast.Nonlocal)]
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<artwork-callback>','exec'),env)
        return env[name]
    def test_deadlines_subtract_callback_work(self):
        state={'idle_frame_deadline':10.0}
        delay=app.external_album_art_next_frame_delay(state,10.006)
        self.assertEqual(11,delay)
        self.assertAlmostEqual(10+1/60,state['idle_frame_deadline'])
        delay=app.external_album_art_next_frame_delay(state,10+1/60+.005)
        self.assertLessEqual(delay,12)
    def test_long_stalls_skip_frames_without_catchup_bursts(self):
        state={'idle_frame_deadline':10.0}
        delay=app.external_album_art_next_frame_delay(state,10.207)
        self.assertGreaterEqual(delay,1);self.assertLessEqual(delay,17)
        self.assertGreater(state['idle_frame_deadline'],10.207)
        self.assertLessEqual(state['idle_frame_deadline']-10.207,1/60+.00001)
    def test_position_only_idle_step_does_not_render_or_save(self):
        root=Mock();state={'last_configure_size':(400,300),'idle_promoted':True,'transient_geometry':'400x300+103+104','native_hwnd':1}
        render=Mock();save=Mock()
        env={'root':root,'state':state,'windows_window_rect':lambda _: (103,104,503,404),
             'schedule_render':render,'save_external_album_art_geometry':save}
        callback=self.extracted('on_configure',env)
        callback(SimpleNamespace(widget=root,width=400,height=300))
        render.assert_not_called();save.assert_not_called()
        self.assertEqual('400x300+103+104',state['last_geometry'])
    def test_actual_resize_keeps_normal_render_path(self):
        root=Mock();state={'last_configure_size':(400,300),'idle_promoted':True,'transient_geometry':'400x300+103+104','native_hwnd':1,'programmatic_geometry':True}
        refresh=Mock(side_effect=RuntimeError('normal rendering path'))
        selfobj=SimpleNamespace(_lock=threading.RLock())
        env={'root':root,'state':state,'windows_window_rect':lambda _: (103,104,603,404),
          '_parse_external_album_art_geometry':app._parse_external_album_art_geometry,
          'self':selfobj,'ctrl_is_down':lambda:False,'schedule_geometry_save':Mock(),
          'refresh_monitor_scaled_chrome':refresh}
        callback=self.extracted('on_configure',env)
        with self.assertRaisesRegex(RuntimeError,'normal rendering path'):
            callback(SimpleNamespace(widget=root,width=500,height=300))
        refresh.assert_called_once()
    def test_unchanged_geometry_after_async_configure_uses_fast_path(self):
        root=Mock();state={'last_configure_size':(400,300),'idle_promoted':True,'aspect_adjusting':True,'native_hwnd':1}
        env={'root':root,'state':state,'windows_window_rect':lambda _: (103,104,503,404)}
        self.extracted('on_configure',env)(SimpleNamespace(widget=root,width=400,height=300))
        self.assertEqual('400x300+103+104',state['last_geometry'])
    def test_motion_speed_is_independent_of_frame_rate(self):
        positions=[]
        for fps in (30,60,120):
            motion={'motion_pattern':1,'motion_last_at':1.0,'motion_x':0.,'motion_y':0.,'motion_target':(1000.,0.)}
            current=(0,0)
            for index in range(1,fps+1):
                current=app.external_album_art_advance_idle_motion(motion,current,(0,0),(0,1000,0,0),pattern=1,pulse=0,music_enabled=False,return_to_origin=False,now=1+index/fps)
            positions.append(motion['motion_x'])
        for position in positions:self.assertAlmostEqual(38,position,places=6)
    def test_schedule_reports_measured_pacing_without_per_frame_logging(self):
        root=Mock();log=Mock();state={'idle_promoted':True,'idle_extra_windows':[], 'idle_frame_stats':{'start':1.,'previous':10.98,'frames':599,'max_gap':.02,'max_work':.004}}
        env={'root':root,'state':state,'time':SimpleNamespace(monotonic=lambda:11.005),
             'append_pafplayer_trace':log,'external_album_art_next_frame_delay':app.external_album_art_next_frame_delay,'idle_art_watch':Mock()}
        self.extracted('schedule_idle_art_frame',env)(11.0)
        log.assert_called_once();self.assertEqual('art.idle.pacing',log.call_args.args[0])
        self.assertEqual(60.,log.call_args.kwargs['fps'])
        self.assertGreaterEqual(root.after.call_args.args[0],1)
    def test_idle_detection_uses_low_rate_and_drops_animation_deadline(self):
        root=Mock();state={'idle_promoted':False,'idle_frame_deadline':1.0};log=Mock()
        env={'root':root,'state':state,'time':SimpleNamespace(monotonic=lambda:2.),'idle_art_watch':Mock(),'append_pafplayer_trace':log}
        self.extracted('schedule_idle_art_frame',env)(1.99)
        self.assertNotIn('idle_frame_deadline',state);self.assertEqual(100,root.after.call_args.args[0]);log.assert_not_called()

if __name__=='__main__':unittest.main()
