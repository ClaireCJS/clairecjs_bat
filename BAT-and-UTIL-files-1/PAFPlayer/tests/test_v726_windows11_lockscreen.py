import ast
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
import PAFPlayer
import PAFPlayer_lockscreen_installer as bundled
import PAFPlayer_remote_lockscreen as remote
from test_v724_remote_lockscreen import Remote, Settings

spec=importlib.util.spec_from_file_location('source_lockscreen_installer_v726',ROOT/'lockscreen'/'lockscreen_installer.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)

class WindowsVersionTests(unittest.TestCase):
    def invoke(self, installer, build, architecture='AMD64', system='Windows'):
        with mock.patch.object(installer.platform,'system',return_value=system), \
             mock.patch.object(installer.sys,'getwindowsversion',return_value=SimpleNamespace(build=build),create=True), \
             mock.patch.dict(installer.os.environ,{'PROCESSOR_ARCHITECTURE':architecture,'PROCESSOR_ARCHITEW6432':''}):
            return installer.require_windows_10()

    def test_source_and_bundle_accept_win11_and_future_builds(self):
        for installer in (source,bundled):
            for build in (19041,22000,26300,99999):
                with self.subTest(installer=installer.__name__,build=build):
                    self.assertIsNone(self.invoke(installer,build))

    def test_still_rejects_old_windows_non_windows_and_unsupported_architecture(self):
        for installer in (source,bundled):
            for kwargs in ({'build':19040},{'build':26300,'architecture':'x86'},{'build':26300,'system':'Linux'}):
                with self.subTest(installer=installer.__name__,**kwargs):
                    with self.assertRaises(installer.InstallerError): self.invoke(installer,**kwargs)

    def test_win11_automatic_inspection_requests_install(self):
        backend=mock.Mock();backend.installed_version.return_value='';backend.trusted.return_value=False;backend.uac_enabled.return_value=True
        with mock.patch.object(bundled.platform,'system',return_value='Windows'), \
             mock.patch.object(bundled.sys,'getwindowsversion',return_value=SimpleNamespace(build=26300),create=True), \
             mock.patch.dict(bundled.os.environ,{'PROCESSOR_ARCHITECTURE':'AMD64','PROCESSOR_ARCHITEW6432':''}), \
             mock.patch.object(bundled,'WindowsBackend',return_value=backend):
            controller=remote.RemoteLockScreen(Remote(),Settings())
            controller.install_async=mock.Mock(return_value=True)
            controller._onboard()
        controller.install_async.assert_called_once_with(automatic=True)

    def test_bundled_sources_match_editable_sources(self):
        tree=ast.parse((ROOT/'PAFPlayer.py').read_text(encoding='utf-8-sig'))
        for name,path in [('PAFPlayer_lockscreen_installer','lockscreen/lockscreen_installer.py'),('PAFPlayer_lockscreen','lockscreen/src/PAFPlayer_lockscreen.py'),('PAFPlayer_remote_lockscreen','src/PAFPlayer_remote_lockscreen.py')]:
            values=[]
            for node in tree.body:
                if not isinstance(node,ast.Assign):continue
                for target in node.targets:
                    if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES' and isinstance(target.slice,ast.Constant) and target.slice.value==name:values.append(ast.literal_eval(node.value))
                    if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES' and isinstance(node.value,ast.Dict):
                        for key,value in zip(node.value.keys,node.value.values):
                            if isinstance(key,ast.Constant) and key.value==name:values.append(ast.literal_eval(value))
            self.assertTrue(values,name);self.assertEqual((ROOT/path).read_text(encoding='utf-8-sig'),values[-1])

if __name__=='__main__':unittest.main()
