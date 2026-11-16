import time
import unittest
from unittest import mock

import PAFPlayer
import PAFPlayer_lockscreen as local
import PAFPlayer_lockscreen_installer as installer
import PAFPlayer_remote_lockscreen as module
from test_v724_remote_lockscreen import Remote, Settings, wait_for

class AutomaticLockscreenTests(unittest.TestCase):
    def controller(self, result, saved=None):
        settings=Settings();settings.values.update(saved or {})
        notices=[]
        controller=module.RemoteLockScreen(Remote(),settings,on_attention=lambda:notices.append('show'),inspector=lambda:result)
        controller.install_async=mock.Mock(return_value=True)
        return controller,notices

    def test_default_on_and_respects_explicit_off(self):
        controller,notices=self.controller(('', '530.0.0.0',False,True))
        self.assertTrue(controller.enabled());controller._onboard()
        controller.install_async.assert_called_once_with(automatic=True)
        self.assertEqual(['show'],notices)
        controller,notices=self.controller(('', '530.0.0.0',False,True),{module.RemoteLockScreen.KEY:False})
        self.assertFalse(controller.enabled());controller._onboard()
        controller.install_async.assert_not_called();self.assertEqual([],notices)

    def test_installed_verified_needs_no_install_and_guide_can_be_acknowledged(self):
        controller,notices=self.controller(('530.0.0.0','530.0.0.0',True,None))
        controller._onboard();controller.install_async.assert_not_called()
        self.assertEqual(['show'],notices);self.assertIn('verified',controller.install_message)
        controller.set_option(controller.GUIDE_KEY,True);notices.clear();controller._onboard()
        controller.install_async.assert_not_called();self.assertFalse(notices)
        newer,notices=self.controller(('531.0.0.0','530.0.0.0',True,None),{module.RemoteLockScreen.GUIDE_KEY:True})
        newer._onboard();newer.install_async.assert_not_called();self.assertFalse(notices)

    def test_uac_disabled_and_unsupported_are_explained_without_install(self):
        controller,notices=self.controller(('', '530.0.0.0',False,False))
        controller._onboard();controller.install_async.assert_not_called()
        self.assertIn('User Account Control is off',controller.install_message);self.assertEqual(['show'],notices)
        controller.inspector=mock.Mock(side_effect=ValueError('Windows build 18363 is too old'))
        controller._onboard();controller.install_async.assert_not_called()
        self.assertIn('18363',controller.install_message)

    def test_startup_checks_even_without_remote_connection_and_reenable_rechecks(self):
        remote=Remote();remote.connected=False;settings=Settings();notices=[]
        inspector=mock.Mock(return_value=('', '530.0.0.0',False,True))
        controller=module.RemoteLockScreen(remote,settings,on_attention=lambda:notices.append('show'),inspector=inspector)
        with mock.patch.object(controller,'install_async',return_value=True) as install:
            controller.start()
            try:
                self.assertTrue(wait_for(lambda: install.call_count==1))
                self.assertFalse(remote.connected)
                controller.set_option(controller.KEY,False)
                controller.set_option(controller.KEY,True)
                self.assertTrue(wait_for(lambda: install.call_count==2))
            finally:controller.close()

    def test_failed_automatic_install_reports_error_and_requests_help(self):
        settings=Settings();notices=[]
        controller=module.RemoteLockScreen(Remote(),settings,on_attention=lambda:notices.append('show'))
        with mock.patch.object(local,'embedded_installer_root',return_value='unused'), mock.patch.object(installer,'WindowsBackend'), mock.patch.object(installer,'install',side_effect=OSError('Windows approval was declined')):
            self.assertTrue(controller.install_async(automatic=True))
            self.assertTrue(wait_for(lambda:not controller.install_busy))
        self.assertIn('approval was declined',controller.install_message)
        self.assertEqual(['show'],notices)

if __name__=='__main__':unittest.main()
