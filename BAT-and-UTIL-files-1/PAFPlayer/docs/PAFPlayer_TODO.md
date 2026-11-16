# PAFPlayer TODO

Only active, unverified follow-up work belongs here. Completed work is retained
in versioned release notes and changelog history.

## Medium priority

- [ ] Migrate the play-history database from the legacy
      `play_audio_file-play-history.sqlite3` name/location to a private PAFPlayer
      subfolder using the requested new filename
      `PAFPlayer-play-history.sqllite3` (confirm whether the `sqllite3` spelling
      is intentional or should be corrected to `sqlite3`). The default root
      should be `C:\util\PAFPlayer\private\`; if `C:\util\` does not exist,
      allow `C:\bat\PAFPlayer\private\` as a fallback, but never select that
      fallback for Claire personally. On startup, detect the old database,
      migrate it safely to the new location/name, verify the migrated database,
      and leave the old file beside itself as a `.bak` rather than deleting it.
      Preserve existing history and avoid overwriting an existing destination
      without a verified backup. Double-check that the relevant `.gitignore`
      rules exclude the new private database and its backups, including the
      publishing copy in `C:\clairecjs_bat` if that repository is the source
      copied for publication.

## Discord Social SDK live validation

- [ ] Enable Social SDK for the PAFPlayer application in Discord's Developer
      Portal using accurate music-player details, then download its official
      Windows C++ package.
- [ ] Build `discord_social/PAFPlayerDiscordSocial.exe` against that package;
      verify OAuth, token refresh, profile updates, privacy clearing, and
      shutdown on a real Discord account without Discord Desktop running.
      V592 provides the source, web controls, and testable Python transport.

## Emoji rendering selector (player and tray client)

- [ ] Verify Whip Emojimaxx on the physical remote client. Floating Lyrics
      stability is confirmed working by the user; Whip itself is unconfirmed.

## Windows media panel verification

- [ ] On the physical Windows 10 lock screen, verify V611's Chrome reassertion
      while PAFPlayer is playing, including the active Nest camera case. Check
      paused, track change, exit, and Chrome resuming after PAFPlayer starts.
      Windows owns final session selection and may still show Chrome.
- [ ] Build and sign a new lock-screen companion package from V611's updated
      `StatusUpdater.cs`, then install it and confirm the three-line formatting
      on the physical lock screen. The existing signed V530 package still shows
      its old text until replaced; the matching signing key is unavailable here.
- [ ] Let a tray-only client manage a local lock-screen companion for its
      verified remote server, with per-machine enablement, owner handoff and
      command routing. Standalone V530 companion setup already supports a
      verified remote hostname manually. Automatic management requires a
      signed companion update; the current managed mode requires a local
      player process and loopback server. The client also needs a local SMTC
      bridge for right-side media controls.


