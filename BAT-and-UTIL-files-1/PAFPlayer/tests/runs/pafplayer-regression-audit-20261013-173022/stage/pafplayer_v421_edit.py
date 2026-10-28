from pafplayer_v416_edit import edit, sub

def transform(s):
    s = sub(s, '2026-09-21-v420-external-media-priority', '2026-09-21-v421-manual-play-override')
    s = sub(s, '"V420"', '"V421"', 2)
    s = sub(s, '"""Own automatic pauses; enabled external-media priority survives Play requests."""',
            '"""Pause for new competing playback; explicit Play acknowledges current sources."""')
    s = sub(s, '        self.last_decision = "starting"\n', '''        self.last_decision = "starting"
        self.baseline_observed = False
        self.acknowledged_sources = set()
        self.source_quiet_since = {}
''')
    s = sub(s, '''        active = bool(snapshot.get("active"))
        known = bool(snapshot.get("known"))
''', '''        sources = set(snapshot.get("active", ()))
        known = bool(snapshot.get("known"))
        # Existing background media is not a new interruption. Wait for actual
        # evidence before establishing the startup baseline (not an empty,
        # unknown startup sample). Acknowledgements belong to individual apps,
        # so a continuing Chrome video cannot suppress a newly started VLC.
        if not self.baseline_observed and (known or sources):
            self.acknowledged_sources.update(sources)
            self.baseline_observed = True
        for source in tuple(self.acknowledged_sources):
            if not known or source in sources:
                self.source_quiet_since.pop(source, None)
            else:
                since = self.source_quiet_since.setdefault(source, now)
                if now - since >= EXTERNAL_MEDIA_RESUME_QUIET_SECONDS:
                    self.acknowledged_sources.remove(source)
                    self.source_quiet_since.pop(source, None)
        active = bool(sources - self.acknowledged_sources)
''')
    s = sub(s, '''            if enabled and active:
                # Play expresses intent to resume after competing playback, not
                # permission to disable priority for the rest of the session.
                self.auto_paused = True
                self.last_decision = "waiting-for-other-media"
                return None if paused else EXTERNAL_MEDIA_PAUSE
            self.auto_paused = False
            self.last_decision = "manual-play"
''', '''            self.acknowledged_sources.update(sources)
            self.source_quiet_since.clear()
            self.auto_paused = False
            self.quiet_since = None
            # Manual Play is immediate, including during a previous auto fade.
            self.fade_total = self.fade_elapsed = 0.0
            self.last_decision = "manual-play"
''')
    s = sub(s, '                "external_media_active": list(self.last_snapshot.get("active", ())),',
               '                "external_media_active": list(self.last_snapshot.get("active", ())),\n                "external_media_acknowledged": sorted(self.acknowledged_sources),')
    s = sub(s, 'Let other media take priority, including YouTube. Resume only a pause made automatically; manual Pause stays paused. Turn this off to play PAFPlayer and other media simultaneously.',
               'Pause for newly active VLC, Winamp or browser playback. Existing background media is ignored at startup. Play resumes immediately and overrides currently active players until they stop; another player can still interrupt. Manual Pause stays paused.')
    s = sub(s, 'Waiting for other media to finish. Pause keeps PAF paused afterward; turn off automatic pause to play both.',
               'Paused for other media. Press Play to resume now, or wait for it to finish. Pause keeps PAF paused afterward.')
    return s

edit(transform)
