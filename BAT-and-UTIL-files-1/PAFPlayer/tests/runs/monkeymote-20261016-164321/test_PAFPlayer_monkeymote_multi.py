"""V568 concurrent emulated clients and live configuration; no mobile certification."""
import json
import socket
import struct
import threading
import time
import types
import unittest
from unittest import mock

import PAFPlayer_monkeymote as mm
from test_PAFPlayer_monkeymote import FakePlayer
import test_PAFPlayer_monkeymote as fixtures


def read_frame(client):
    def exact(count):
        result = b''
        while len(result) < count:
            data = client.recv(count-len(result))
            if not data: raise EOFError('Peer closed')
            result += data
        return result
    magic, kind, size = mm.HEADER.unpack(exact(12))
    assert magic == mm.MAGIC
    return kind, exact(size)


def connect(port, authenticate=True):
    client = socket.create_connection(('127.0.0.1', port), timeout=2)
    try:
        assert read_frame(client)[0] == 1
        if authenticate:
            client.sendall(mm.packet(2, bytes(16)+b'\1\1'))
            for expected in (3, 23, 5, 11, 36, 6, 28):
                assert read_frame(client)[0] == expected
        return client
    except BaseException:
        client.close()
        raise


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class MultiClientTests(unittest.TestCase):
    def test_two_authenticated_clients_and_slow_peer_are_independent(self):
        player = FakePlayer()
        listener = mm.Listener(player, mm.validate_config(dict(enabled=True, port=free_port()))).start()
        self.addCleanup(listener.close)
        clients = [connect(listener.socket.getsockname()[1], auth) for auth in (False, True, True)]
        for client in clients: self.addCleanup(client.close)
        self.assertEqual(3, listener.client_count())
        for index, client in enumerate(clients[1:]):
            client.sendall(mm.packet(4, struct.pack('<BI', 4, 0)))
            self.assertEqual(9, read_frame(client)[0])
            client.sendall(mm.packet(7, struct.pack('<BI', 6, 50+index)))
        deadline = time.monotonic()+2
        while len(player.actions)<2 and time.monotonic()<deadline: time.sleep(.01)
        self.assertCountEqual([(6,50),(6,51)], player.actions)
        clients[1].close()
        clients[2].sendall(mm.packet(46))
        self.assertEqual(23, read_frame(clients[2])[0])
        listener.close()
        self.assertFalse(listener.is_running())
        self.assertEqual(0, listener.client_count())

    def test_client_limit_is_bounded_and_ownership_loss_closes_all(self):
        player = FakePlayer()
        listener = mm.Listener(player, mm.validate_config(dict(enabled=True, port=free_port()))).start()
        self.addCleanup(listener.close)
        for _ in range(mm.MAX_CLIENTS):
            client = connect(listener.socket.getsockname()[1], False)
            self.addCleanup(client.close)
        extra = socket.create_connection(listener.socket.getsockname(), timeout=2)
        self.addCleanup(extra.close)
        self.assertEqual(b'', extra.recv(1))
        player.official = False
        deadline = time.monotonic()+2
        while listener.client_count() and time.monotonic()<deadline: time.sleep(.02)
        self.assertEqual(0, listener.client_count())

    def test_clients_have_separate_caches_and_atomic_shared_transport_gate(self):
        adapter, server, runtime = fixtures.AdapterTests().adapter()
        server._state.update(playing=True, track={'path':'a.flac'})
        runtime.monkeymote_queue_read=lambda:dict(entries=['a.flac','b.flac'],current='a.flac')
        a, b = adapter.for_client(), adapter.for_client()
        a.playlist()
        self.assertEqual((), b.playlist_token())
        barrier = threading.Barrier(3)
        results = []
        def press(client):
            barrier.wait()
            results.append(client.command(8))
        threads = [threading.Thread(target=press,args=(client,)) for client in (a,b)]
        for thread in threads: thread.start()
        barrier.wait()
        for thread in threads: thread.join(2)
        self.assertCountEqual([True,False], results)
        self.assertEqual('next-file',server.pop_action())
        self.assertIsNone(server.pop_action())

    def test_missed_pause_ack_does_not_permanently_block_other_client(self):
        adapter, server, _ = fixtures.AdapterTests().adapter()
        server._state.update(playing=True, paused=False)
        with mock.patch.object(mm.time,'monotonic',return_value=1):
            self.assertTrue(adapter.for_client().command(2))
        self.assertEqual('web-pause',server.pop_action())
        server.publish(paused=True)
        server.publish(paused=False)  # Local keyboard resumed before next phone poll.
        with mock.patch.object(mm.time,'monotonic',return_value=2):
            self.assertTrue(adapter.for_client().command(8))
        self.assertEqual('next-file',server.pop_action())


class ConfigurationTests(unittest.TestCase):
    def controller(self, settings=None, options=None):
        player=FakePlayer()
        player.runtime=types.SimpleNamespace(settings=settings or {},save_settings=mock.Mock())
        player.server=types.SimpleNamespace()
        controller=mm.Controller(player,dict(host='127.0.0.1',trusted_subnet='127.0.0.0/8',port=free_port(),**(options or {})))
        self.addCleanup(controller.close)
        return controller

    def test_default_enabled_and_cli_port_validation(self):
        self.assertEqual((['song.flac'],{}),mm.parse_options(['song.flac']))
        rest, values=mm.parse_options(['--monkeymote-port','19372','song.flac'])
        self.assertEqual(['song.flac'],rest)
        self.assertEqual(19372,values['_cli_port'])
        for args in (['--monkeymote-port'],['--monkeymote-port=80'],['--monkeymote-port=65536'],['--monkeymote-port=x'],['--monkeymote-port=19371','--monkeymote-port=19372']):
            with self.assertRaises(ValueError): mm.parse_options(args)
        self.assertTrue(self.controller().enabled)

    def test_saved_choices_and_cli_precedence_and_explicit_nonowner(self):
        c=self.controller({'monkeymote':{'enabled':False,'port':19372}}, {'_cli_port':19373})
        self.assertFalse(c.enabled)
        self.assertEqual(19373,c.config['port'])
        c.start()
        self.assertIsNone(c.listener)
        c.adapter.official=False
        with self.assertRaises(PermissionError): c.configure({'enabled':True})

    def test_live_port_handoff_and_collision_preserve_old_listener_and_settings(self):
        c=self.controller().start()
        old=c.listener
        phone=connect(c.config['port'])
        self.addCleanup(phone.close)
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1',0)); occupied.listen()
            with self.assertRaises(OSError): c.configure({'port':occupied.getsockname()[1],'permanent':True})
        self.assertIs(old,c.listener)
        c.runtime.save_settings.assert_not_called()
        phone.sendall(mm.packet(46)); self.assertEqual(23,read_frame(phone)[0])
        new_port=free_port()
        c.configure({'port':new_port,'permanent':False})
        self.assertFalse(old.is_running())
        new_phone=connect(new_port)
        self.addCleanup(new_phone.close)
        self.assertEqual(b'',phone.recv(1))
        c.runtime.save_settings.assert_not_called()

    def test_save_failure_rolls_back_candidate_listener_and_prior_settings(self):
        c=self.controller().start()
        old=c.listener; port=c.config['port']
        c.runtime.save_settings.side_effect=OSError('No space')
        with self.assertRaises(OSError): c.configure({'port':free_port(),'permanent':True})
        self.assertIs(old,c.listener)
        self.assertEqual(port,c.config['port'])
        self.assertNotIn('monkeymote',c.runtime.settings)
        self.assertTrue(c.listener.is_running())

    def test_permanent_disable_requires_confirmation_and_session_change_does_not_save(self):
        c=self.controller().start()
        with self.assertRaises(ValueError): c.configure({'enabled':False,'permanent':True})
        self.assertTrue(c.listener.is_running())
        c.configure({'enabled':False,'permanent':False})
        self.assertIsNone(c.listener)
        c.runtime.save_settings.assert_not_called()
        c.configure({'enabled':False,'permanent':True,'confirm_disable':True})
        self.assertEqual(False,c.runtime.settings['monkeymote']['enabled'])
        c.runtime.save_settings.assert_called_once()
        c.configure({'enabled':True,'permanent':True})
        self.assertTrue(c.listener.is_running())
        self.assertTrue(c.runtime.settings['monkeymote']['enabled'])

    def test_local_authenticated_http_configuration(self):
        import io
        from PAFPlayer_web_workflows import handle
        c=self.controller().start()
        runtime=c.runtime
        runtime.monkeymote=c
        runtime.token='test-token'
        runtime.log=mock.Mock()
        owner=types.SimpleNamespace(host='127.0.0.1',port=666,workflows=runtime)
        def request(payload, token='test-token', local=True, origin='http://127.0.0.1:666'):
            raw=json.dumps(payload).encode()
            handler=types.SimpleNamespace(command='POST',path='/api/workflows/monkeymote',
                headers={'Host':'127.0.0.1:666','Origin':origin,'X-PAF-Workflow-Token':token,'Content-Length':str(len(raw))},
                _client_is_local=lambda:local,connection=mock.Mock(),rfile=io.BytesIO(raw),_json=mock.Mock())
            self.assertTrue(handle(handler,owner,handler.path))
            return handler._json.call_args.args
        self.assertEqual(403,request({'enabled':False},token='bad')[0])
        self.assertEqual(403,request({'enabled':False},origin='http://evil.invalid')[0])
        runtime.settings['remote_uploads']=True
        self.assertEqual(403,request({'enabled':False},local=False)[0])
        self.assertTrue(c.listener.is_running())
        code,data=request({'enabled':False,'permanent':False})
        self.assertEqual(200,code)
        self.assertFalse(data['listening'])

    def test_web_controls_in_rendered_page_and_bundle(self):
        import PAFPlayer as app
        from pathlib import Path
        page=app._paf_web_html()
        self.assertIn("['monkeyMoteSection','MonkeyMote']",page)
        for phrase in ('Enable MonkeyMote compatibility','19371','This run only','Save for future runs','confirm_disable','/api/workflows/monkeymote'):
            self.assertIn(phrase,page)
        for name in ('PAFPlayer_monkeymote','PAFPlayer_workflows_ui','PAFPlayer_web_workflows'):
            self.assertEqual(Path(name+'.py').read_text(encoding='utf-8'),app._PAF_BUNDLED_SOURCES[name])


if __name__=='__main__': unittest.main()
