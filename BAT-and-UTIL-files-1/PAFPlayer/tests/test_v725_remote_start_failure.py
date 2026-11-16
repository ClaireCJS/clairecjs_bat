import unittest
from unittest import mock
import PAFPlayer
import PAFPlayer_lockscreen as local
import PAFPlayer_remote_lockscreen as module
from test_v724_remote_lockscreen import Remote, Settings, wait_for

class StartFailureTests(unittest.TestCase):
    def test_publisher_failure_opens_help_even_after_guide_acknowledged(self):
        settings=Settings();settings.values[module.RemoteLockScreen.GUIDE_KEY]=True
        notices=[]
        def fail(*args): raise OSError('Windows activation failed')
        controller=module.RemoteLockScreen(Remote(),settings,launcher=fail,
            on_attention=lambda:notices.append('help'),inspector=lambda:('530.0.0.0','530.0.0.0',True,None))
        with mock.patch.object(local,'installed_version',return_value='530.0.0.0'):
            controller.start()
            try:
                self.assertTrue(wait_for(lambda:bool(notices)))
                self.assertIn('Windows activation failed',controller.status)
            finally:controller.close()

if __name__=='__main__':unittest.main()
