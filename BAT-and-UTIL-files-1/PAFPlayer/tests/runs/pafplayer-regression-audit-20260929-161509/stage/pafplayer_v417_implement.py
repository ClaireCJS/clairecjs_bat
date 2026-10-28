"""Apply V417 with verified replacement backups."""
from pafplayer_v416_edit import edit, sub


def transform(s):
    s = sub(s, '"2026-09-20-v416-timelines-todos-external-media"', '"2026-09-21-v417-wawi-controls-and-downloads"')
    s = sub(s, 'PROGRAM_VERSION                 = "V416"', 'PROGRAM_VERSION                 = "V417"')
    s = sub(s, 'WEB_PAUSE                       = "web-pause"', 'WEB_PAUSE                       = "web-pause"\nWEB_STOP                        = "web-stop"  # Stop/reset without exiting the HTTP session.')
    s = sub(s, 'if action in {PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE}:', 'if action in {PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP}:')
    s = sub(s, 'actions.update({WEB_PLAY, WEB_PAUSE, WEB_OPEN_TRACK_FOLDER,', 'actions.update({WEB_PLAY, WEB_PAUSE, WEB_STOP, WEB_OPEN_TRACK_FOLDER,')
    s = sub(s, 'STOP, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, PREVIOUS_FILE, NEXT_FILE,', 'STOP, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP, PREVIOUS_FILE, NEXT_FILE,')
    s = sub(s, 'class PAFWebServer:', '''def paf_web_client_is_local(peer_address: str, server_address: str) -> bool:
    """Classify the TCP peer, including LAN and IPv4-mapped IPv6 connections.

    Never trust Host or X-Forwarded-For to authorize opening an Explorer window.
    """
    import ipaddress
    try:
        peer = ipaddress.ip_address(str(peer_address).split("%", 1)[0])
        local = ipaddress.ip_address(str(server_address).split("%", 1)[0])
        peer = getattr(peer, "ipv4_mapped", None) or peer
        local = getattr(local, "ipv4_mapped", None) or local
        return peer.is_loopback or peer == local
    except ValueError:
        return False


def paf_web_download_disposition(filename: str) -> str:
    """RFC 6266 UTF-8 filename plus a safe ASCII fallback."""
    from urllib.parse import quote
    name = "".join(c for c in filename if ord(c) >= 32 and ord(c) != 127)
    fallback = "".join(c if 32 <= ord(c) < 127 and c not in '\\\\"/;' else "_" for c in name)
    return f'attachment; filename="{fallback or "audio"}"; filename*=UTF-8\\'\\'{quote(name or "audio", safe="")}'


class PAFWebServer:''')
    s = sub(s, '            def _send(self, status: int, body: bytes, content_type: str) -> None:', '''            def _client_is_local(self) -> bool:
                return paf_web_client_is_local(self.client_address[0], self.connection.getsockname()[0])

            def _send(self, status: int, body: bytes, content_type: str) -> None:''')
    s = sub(s, '                self.send_header("X-PAF-Server-Time", str(time.time()))\n                self.end_headers()\n                self.wfile.write(body)', '''                self.send_header("X-PAF-Server-Time", str(time.time()))
                self.send_header("X-PAF-Client-Local", "1" if self._client_is_local() else "0")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)''')
    s = sub(s, '            def do_GET(self):\n                path, _separator, query = self.path.partition("?")', '''            def _download_audio(self):
                # Snapshot/open once: advancing the playlist cannot switch a transfer.
                import mimetypes
                import stat
                audio = owner.current_audio()
                if audio is None:
                    self._json(404, {"error": "no current audio file"}); return
                try:
                    stream = audio.open("rb")
                except (FileNotFoundError, IsADirectoryError):
                    self._json(404, {"error": "current audio file is unavailable"}); return
                except OSError:
                    self._json(403, {"error": "current audio file cannot be read"}); return
                with stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode):
                        self._json(404, {"error": "current audio is not a file"}); return
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type(audio.name)[0] or "application/octet-stream")
                    self.send_header("Content-Length", str(info.st_size))
                    self.send_header("Content-Disposition", paf_web_download_disposition(audio.name))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    if self.command == "HEAD":
                        return
                    remaining = info.st_size
                    try:
                        while remaining:
                            chunk = stream.read(min(128 * 1024, remaining))
                            if not chunk:
                                self.close_connection = True
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                    except OSError:
                        # Browser cancellation/file removal must not affect playback.
                        self.close_connection = True

            def do_HEAD(self):
                # winamp-*.bat uses wget32 --spider: HEAD must execute exactly once.
                self.do_GET()

            def do_GET(self):
                path, _separator, query = self.path.partition("?")
                legacy_actions = {"/play": WEB_PLAY, "/pause": PAUSE_TOGGLE,
                                  "/unpause": WEB_PLAY, "/stop": WEB_STOP,
                                  "/next": NEXT_FILE, "/prev": PREVIOUS_FILE,
                                  "/previous": PREVIOUS_FILE}
                if path in legacy_actions:
                    owner.note_client_activity()
                    accepted = owner.enqueue_action(legacy_actions[path])
                    self._json(200 if accepted else 503, {"accepted": accepted, "action": legacy_actions[path]})
                    return
                if path == "/main" or (path == "/winamp" and "page=main" in query.split("&")):
                    import html
                    state = owner.snapshot()
                    if state.get("transport_stopped") or not state.get("playing"):
                        # Both the Perl parser and BAT fast parser have case-sensitive matches.
                        label = "Winamp is stopped at track 1 (Stopped at track 1)"
                    elif state.get("paused"):
                        label = "Paused in track 1"
                    else:
                        label = "Playing track 1"
                    name = str(state.get("track", {}).get("filename", ""))
                    # Keep names on a separate line so a name cannot spoof the legacy parser.
                    body = "<!doctype html><meta charset=utf-8><title>PAFPlayer status</title>\\n<p>" + html.escape(name) + "</p>\\n<p>" + label + "</p>\\n"
                    self._send(200, body.encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/api/audio/download":
                    self._download_audio()
                    return''')
    s = sub(s, '                    action = str(payload.get("action", ""))\n                    accepted = owner.enqueue_action(action)', '''                    action = str(payload.get("action", ""))
                    if action == WEB_OPEN_TRACK_FOLDER and not self._client_is_local():
                        self._json(403, {"accepted": False, "error": "folder opening is available on the player computer"})
                        return
                    accepted = owner.enqueue_action(action)''')
    s = sub(s, '            self._state.update({\n                "playing": True,\n                "paused": False,', '            self._state.update({\n                "playing": True,\n                "paused": False,\n                "transport_stopped": False,')
    s = sub(s, '            self._state.update(values)\n            self._state["updated_at_epoch"]', '''            self._state.update(values)
            if values.get("paused") is False and values.get("playing") is True:
                self._state["transport_stopped"] = False
            if self._state.get("transport_stopped"):
                self._state["playing"] = False
            self._state["updated_at_epoch"]''')
    s = sub(s, '                if action == PAUSE_TOGGLE:\n                    record_segment(displayed_position)', '                if action in {PAUSE_TOGGLE, WEB_STOP}:\n                    record_segment(displayed_position)')
    s = sub(s, '''                    stop_process(process)
                    header_paused = True''', '''                    stop_process(process)
                    if action == WEB_STOP:
                        position = playback_start
                        if playback_position_state is not None:
                            playback_position_state[0] = position
                        if web_server is not None:
                            web_server.publish(transport_stopped=True, playing=False, paused=True,
                                               position_seconds=0.0, progress=0.0)
                    header_paused = True''')
    s = sub(s, '''                        if paused_action == WEB_PAUSE:
                            paused_action = None''', '''                        if paused_action == WEB_STOP:
                            position = playback_start
                            if playback_position_state is not None:
                                playback_position_state[0] = position
                            if web_server is not None:
                                web_server.publish(transport_stopped=True, playing=False, paused=True,
                                                   position_seconds=0.0, progress=0.0)
                            render_static_header(position)
                            show_status(position, "⏹️")
                            continue
                        if paused_action == WEB_PAUSE:
                            paused_action = None''')
    s = sub(s, '<button class="wawi stop" onclick="action(\'stop\')" title="Stop">■</button>', '<button class="wawi stop" onclick="action(\'web-stop\')" title="Stop and return to the beginning">■</button>')
    s = sub(s, '.path{word-break:break-all;color:#95e6b5}', '''.path{word-break:break-all;color:#95e6b5;text-decoration:none}.path:hover{text-decoration:underline}
.track-file{display:flex;align-items:baseline;gap:6px;min-width:0}.track-file .path{min-width:0}.track-download{flex:none;color:#95e6b5;text-decoration:none;font-size:15px;line-height:1;padding:3px 5px;border:1px solid #ffffff30;border-radius:4px}.track-download:hover{background:#ffffff20}.track-download[hidden]{display:none}''')
    s = sub(s, '<div class="path-url-row"><div class="path" id="path" title="Click filename/path to open this track’s folder in Explorer"></div><div id="urls"></div></div>', '<div class="path-url-row"><div class="track-file"><a class="path" id="path"></a><a class="track-download" id="trackDownload" href="/api/audio/download" download title="Download current audio file" aria-label="Download current audio file" hidden>↓</a></div><div id="urls"></div></div>')
    old = '''  const pathHost=document.getElementById('path');
  const pathText=t.path||'';
  if(pathHost.textContent!==pathText) pathHost.textContent=pathText;
  pathHost.onclick=pathText?()=>action('web-open-track-folder'):null;pathHost.style.cursor=pathText?'pointer':'default';'''
    s = sub(s, old, "  updateTrackLinks(t,response.headers.get('X-PAF-Client-Local')==='1');")
    anchor = "  updateTrackLinks(t,response.headers.get('X-PAF-Client-Local')==='1');"
    # Place a named function outside tick for both UI reuse and behavioral testing.
    pos = s.rfind('async function ', 0, s.index(anchor))
    s = s[:pos] + '''function updateTrackLinks(track,isLocal){
 const pathHost=document.getElementById('path'),download=document.getElementById('trackDownload');
 const pathText=track.path||'';
 if(pathHost.textContent!==pathText)pathHost.textContent=pathText;
 download.hidden=!pathText;
 pathHost.onclick=null;
 if(!pathText){pathHost.removeAttribute('href');pathHost.removeAttribute('download');pathHost.title='';return;}
 pathHost.href=isLocal?'#':'/api/audio/download';
 pathHost.title=isLocal?'Open this track’s folder in Explorer':'Download this audio file';
 if(isLocal){
  pathHost.removeAttribute('download');
  pathHost.onclick=event=>{event.preventDefault();action('web-open-track-folder');};
 }else pathHost.setAttribute('download','');
}
''' + s[pos:]
    return s


if __name__ == '__main__':
    edit(transform)
