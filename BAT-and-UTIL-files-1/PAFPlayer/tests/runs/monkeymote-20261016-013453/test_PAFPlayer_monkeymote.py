"""Wire/client emulation and official-owner tests; not real-device certification.

Golden bytes use the signed Winamp 2.5.0 plug-in's recovered format. The request
sequence was observed from the user's MonkeyMote Music Remote HD iPad.
"""
import hashlib
import socket
import struct
import threading
import types
import unittest
from unittest import mock

import PAFPlayer_monkeymote as mm


class FakePlayer:
    def __init__(self):
        self.official = True
        self.actions = []
        self.state = dict(playing=True, paused=False, volume=50, position_seconds=61,
                          duration_seconds=120, metadata={'Song': 'Title', 'Artist': 'Artist'}, track={})
    def owns(self): return self.official
    def snapshot(self):
        if not self.official: raise PermissionError('Lost owner')
        return dict(self.state)
    def playlist(self): return ['First', 'Second'], 0
    def playlist_token(self): return ('first.flac', 'second.flac')
    def play_selected(self, token, index):
        if not token or not 0 <= index < len(token): return False
        self.actions.append(('selected', token[index])); return True
    def command(self, command, value):
        self.actions.append((command, value)); return True


class ProtocolTests(unittest.TestCase):
    def session(self, password=b''):
        player = FakePlayer()
        session = mm.Session(player, password, nonce=b'12345678')
        return player, session

    def authenticate(self, session):
        digest = hashlib.md5(session.password+b'12345678').digest()
        return session.receive(2, digest+b'\x01\x01')

    def test_greeting_golden_bytes(self):
        _, s = self.session(b'secret')
        self.assertEqual(bytes.fromhex('3b87d971010000000b0000000203013132333435363738'), s.greeting())

    def test_fragmented_and_coalesced_client_frames(self):
        # Auth, modern current-playlist request, Pause: real iPad message shapes.
        frames = bytes.fromhex('3b87d9710200000012000000')+bytes(16)+b'\1\1'
        frames += bytes.fromhex('3b87d97104000000090000000affffffff01000000')
        frames += bytes.fromhex('3b87d97107000000050000000200000000')
        parser = mm.Frames(); parsed = []
        for byte in frames: parsed.extend(parser.feed(bytes([byte])))
        self.assertEqual([2, 4, 7], [x[0] for x in parsed])
        self.assertEqual(parsed, mm.Frames().feed(frames))

    def test_invalid_magic_and_oversized_payload(self):
        for head in (struct.pack('<III', 0, 2, 16), mm.HEADER.pack(mm.MAGIC, 2, mm.MAX_INPUT+1)):
            with self.assertRaises(ValueError): mm.Frames().feed(head)

    def test_password_and_pre_auth_commands(self):
        player, s = self.session(b'secret')
        with self.assertRaises(ValueError): s.receive(7, b'\2'+bytes(4))
        self.assertFalse(s.authenticated)
        self.assertEqual([], player.actions)
        self.assertEqual(mm.packet(3, b'\0'), s.receive(2, bytes(18))[0])
        self.assertEqual(mm.packet(3, b'\1'), self.authenticate(s)[0])

    def test_initial_messages_include_heartbeat_track_state_capabilities(self):
        _, s = self.session()
        kinds = [mm.HEADER.unpack_from(p)[1] for p in self.authenticate(s)]
        self.assertEqual([3, 23, 5, 11, 6, 28], kinds)
        self.assertEqual([], s.receive(23, b''))
        self.assertEqual([mm.packet(23)], s.receive(46, b''))

    def test_current_track_utf8_lengths_and_state(self):
        state = FakePlayer().state
        state['metadata'] = {'Song': '🎵'*100, 'Artist': 'A\0B', 'Album': 'Album'}
        data = mm.track_packet(state)[12:]
        fields = data[35:].split(b'\0')
        self.assertEqual([252, 3, 5, 0], list(data[31:35]))
        self.assertEqual('🎵'*63, fields[0].decode('utf-8'))
        self.assertEqual(b'A B', fields[1])
        self.assertEqual(2, data[30])
        position, status, _, _, volume8, volume16 = struct.unpack('<IBBBBH', mm.state_packet(state)[12:])
        self.assertEqual((61000, 1, 127, 32768), (position, status, volume8, volume16))
        state['paused'] = True
        self.assertEqual(2, mm.state_packet(state)[16])
        state['transport_stopped'] = True
        self.assertEqual(3, mm.state_packet(state)[16])

    def test_real_ipad_request_sequence_and_modern_playlist(self):
        _, s = self.session(); self.authenticate(s)
        result = s.receive(4, struct.pack('<BI', 19, 0))
        self.assertEqual(51, mm.HEADER.unpack_from(result[0])[1])
        self.assertEqual([], s.receive(22, bytes(16)))
        data = s.receive(4, struct.pack('<BII', 10, 0xffffffff, 1))[0]
        self.assertEqual(50, mm.HEADER.unpack_from(data)[1])
        count, playlist_id, size, flags = struct.unpack_from('<IIHB', data, 12)
        self.assertEqual((2, 0xffffffff, 9, 1), (count, playlist_id, size, flags))
        first = 12+12+size
        self.assertEqual(5, struct.unpack_from('<H', data, first+24)[0])
        self.assertEqual(b'First\0\0\0\0', data[first+32:first+41])
        self.assertIn(b'Second', data)

    def test_playlist_selection_uses_advertised_list(self):
        player, s = self.session(); self.authenticate(s)
        s.receive(4, struct.pack('<BI', 4, 0))
        s.receive(7, struct.pack('<BI', 10, 1))
        self.assertEqual([], player.actions)
        s.receive(7, struct.pack('<BI', 1, 0))
        self.assertEqual([('selected', 'second.flac')], player.actions)
        s.receive(7, struct.pack('<BI', 10, 99))
        s.receive(7, struct.pack('<BI', 1, 0))
        self.assertEqual(1, len(player.actions))

    def test_ownership_loss_rejects_commands(self):
        player, s = self.session(); self.authenticate(s)
        player.official = False
        with self.assertRaises(PermissionError): s.receive(7, b'\2'+bytes(4))
        with self.assertRaises(PermissionError): s.updates()
        self.assertEqual([], player.actions)

    def test_volume_legacy_and_extended(self):
        for wire, expected in [(0, 0), (255, 100), (128, 50), (65535<<16, 100), (32768<<16, 50)]:
            self.assertEqual(expected, mm.volume_percent(wire))

    def test_trusted_network_config_and_opt_in(self):
        self.assertEqual((['song.flac'], None), mm.parse_options(['song.flac']))
        self.assertIsNone(mm.validate_config({}))
        good = dict(enabled=True, host='192.168.0.17', trusted_subnet='192.168.0.0/24')
        self.assertEqual('192.168.0.17', mm.validate_config(good)['host'])
        for changed in [dict(host='0.0.0.0'), dict(host='8.8.8.8'), dict(trusted_subnet='0.0.0.0/0'),
                        dict(trusted_subnet='192.168.1.0/24'), dict(enabled='true'), dict(port=True),
                        dict(password='ü')]:
            with self.assertRaises(ValueError): mm.validate_config(dict(good, **changed))

    def test_actual_socket_with_emulated_monkeymote_client(self):
        # socketpair uses loopback on Windows; no firewall or live player involved.
        config = mm.validate_config(dict(enabled=True))
        player = FakePlayer(); listener = mm.Listener(player, config)
        client, server = socket.socketpair()
        worker = threading.Thread(target=listener.serve, args=(server,), daemon=True)
        worker.start()
        client.settimeout(3)
        def read():
            data = b''
            while len(data) < 12: data += client.recv(12-len(data))
            magic, kind, size = mm.HEADER.unpack(data)
            body = b''
            while len(body) < size: body += client.recv(size-len(body))
            self.assertEqual(mm.MAGIC, magic)
            return kind, body
        try:
            kind, hello = read(); self.assertEqual(1, kind)
            auth = mm.packet(2, hashlib.md5(hello[3:]).digest()+b'\1\1')
            client.sendall(auth[:7]); client.sendall(auth[7:])
            self.assertEqual((3, b'\1'), read())
            client.sendall(mm.packet(7, b'\2'+bytes(4)))
            for _ in range(10):
                if player.actions: break
                threading.Event().wait(.05)
            self.assertEqual([(2, 0)], player.actions)
        finally:
            listener.stop_event.set(); client.close(); server.close(); worker.join(1)


class AdapterTests(unittest.TestCase):
    def adapter(self, explicit=False, owns=True):
        import PAFPlayer as app
        owner = types.SimpleNamespace(identity='official', owns=lambda: owns)
        runtime = types.SimpleNamespace(instance=owner)
        server = app.PAFWebServer(enabled=False)
        return mm.PlayerAdapter(app, runtime, server, explicit_instance=explicit), server, runtime

    def test_controls_enter_existing_player_queue(self):
        adapter, server, _ = self.adapter()
        for command, value, expected in [(1, 0, 'web-play'), (2, 0, 'pause-toggle'),
                                          (8, 0, 'next-file'), (9, 0, 'previous-file')]:
            self.assertTrue(adapter.command(command, value))
            self.assertEqual(expected, server.pop_action())
        self.assertTrue(adapter.command(6, 32768<<16))
        self.assertEqual('web-set:volume:50', server.pop_action())
        self.assertFalse(adapter.command(3))

    def test_explicit_secondary_and_replaced_identity_are_rejected(self):
        for explicit, owns in [(True, True), (True, False), (False, False)]:
            adapter, server, _ = self.adapter(explicit, owns)
            self.assertFalse(adapter.owns())
            self.assertFalse(adapter.command(2))
            with self.assertRaises(PermissionError): mm.Listener(adapter, mm.validate_config(dict(enabled=True))).start()
            self.assertIsNone(server.pop_action())
        adapter, server, runtime = self.adapter()
        runtime.instance.identity = 'new-owner'
        self.assertFalse(adapter.command(2))
        self.assertIsNone(server.pop_action())

    def test_selection_is_revision_checked_and_queued(self):
        adapter, server, runtime = self.adapter()
        state = {'entries': ['a.flac', 'b.flac'], 'revision': 'abc'}
        with mock.patch('PAFPlayer_web_workflows.queue_snapshot', return_value=state), \
             mock.patch('PAFPlayer_web_workflows.edit_queue') as edit:
            self.assertFalse(adapter.play_selected(('old.flac',), 0))
            edit.assert_not_called()
            self.assertTrue(adapter.play_selected(('a.flac', 'b.flac'), 1))
            edit.assert_called_once_with(runtime, {'op': 'next', 'paths': ['b.flac'], 'revision': 'abc'})
            self.assertEqual('next-file', server.pop_action())
            self.assertEqual('web-play', server.pop_action())


if __name__ == '__main__': unittest.main()
