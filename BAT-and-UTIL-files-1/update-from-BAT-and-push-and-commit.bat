@Echo Off
rem                      edit this file only as %PUBCL%\DEV\py\clairecjs_bat\update-from-BAT-and-push-and-commit.bat and not the copy in c:\bat\!
@on break cancel
cls

:DESCRIPTION:  WHAT IS THIS?
:DESCRIPTION:                I actually do all my development for this in my personal live command line environment,
:DESCRIPTION:                so for me, these files actually "live" in "c:\bat\" and need to be copied/refreshed to 
:DESCRIPTION:                my local GIT repo beore uploading to GitHub. This script does that.


:USAGE: update-from-BAT-and-push-and-commit [git] [skip-update] 
:USAGE:                                     ^^^^^^^^^^^^^^^^^^^ extra args have to be given in that order





rem CONFIGURATION:
        set TARGET_MAIN=BAT-and-UTIL-files-1
        set TARGET_1=%TARGET_MAIN%
        set TARGET_2=BAT-and-UTIL-files-2
        set COMMIT_CONFIRMATION_WAIT_TIME=5
        set COMMIT_CONFIRMATION_WAIT_TIME=4

        SET MANIFEST_FILES=NONE

        rem Only add files that live in C:\BAT\ to this list:        
        set SECONDARY_BAT_FILES=set-colors.bat bigecho.bat print-message.bat advice.bat celebration.bat debug.bat download-youtube-album.bat error.bat errorlevel.bat fatalerror.bat important.bat important_less.bat less_important.bat logging.bat none.bat print-if-debug.bat print-message.bat removal.bat set-randomfile.bat subtle.bat success.bat unimportant.bat warning.bat warning_soft.bat validate-in-path.bat validate-environment-variables.bat validate-environment-variable.bat validate-env-var.bat update-from-BAT-via-manifest.bat white-noise.bat randcolor.bat randfg.bat randbg.bat emoji-search.bat emoji-grep.bat emoji.env set-emojis.bat set-tmp-file.bat set-tmpfile.bat rename-folders-with-hyphens-into-underscores.bat sort-pictures-into-folders.bat sort-pictures-into-folders-helper.pl fix_unicode_filenames.py sort.bat environm.btm cut.bat generate-filelists-by-attribute.pl generate-filelists-by-attribute-audio.ini generate-audio-playlists.bat makeimg.pl after.bat before.bat set-randomfile.bat set-user-account-to-automatically-login.bat set-temp-folder.bat create-and-change-into-temp-folder.bat set-random-file.bat set-latest-filename.bat set-first-file.bat set-largest-filename.bat set-file-age.bat watch.bat fix-file-dates-using-filenames.bat process-done-torrent.btm copy-move-post.py map-drives.btm checkmappings.bat allfiles.bat allfile2.pl allfilea2w.pl allfileexif.pl allfilef2w.pl allfilefiledate.pl allfilem.pl allfilem2w.pl allfilemp2w.pl allfiles-helper.bat allfiles-prescript-template.pl allfiles-snoop.bat allfilesHyphenswap.pl allfilesmv.pl allfileunicode.pl allfilew2a.pl allfilew2m.pl setpath.bat setprompt.bat prompt-common.bat prompt-claire.bat prompt-carolyn.bat prompt-work.bat echo-rainbow.bat rainbow-echo.bat detect-with-which.bat download-youtube-album.bat highlight.bat wrapper.bat display-date-and-time-nicely.bat backup-repositories.bat backup-repository.bat sync-a-folder-to-somewhere.bat git-add-every-damn-file.bat git-add.bat git-commit-history.bat git-commit.bat commit.bat git-config-set-commit-preference-to-rebase.bat git-config-set-commit-preferences-to-rebase.bat git-history.bat git-init-remote-link-local-project-to-remote-git-repo.bat git-init.bat git-initvars.bat git-link.bat git-log-normal.bat git-log-oneline.bat git-log.bat git-push.bat push.bat git-rename-branch.bat git-revisions.bat git-setvars.bat git-show.bat git-summary.bat git-suppress-CRLF-warning.bat git-timecapsule.bat git-win.bat git.bat checkusername.bat check-for-applications-and-programs-that-can-be-upgraded.bat checkusername.bat randline.pl randline.bat change-into-random-dir.bat randir.bat color.bat colors.bat colors-all.bat add-ReplayGain-tags-to-all-FLACs.bat add-ReplayGain-tags-to-all-mp3s.bat add-ReplayGain-tags.bat list-flac-replaygain-tags.bat list-flac-tags.bat list-all-mp3-tags.bat list-mp3-replaygain-tags.bat list-replaygain-tags-in-all-flac-files.bat list-replaygain-tags.bat sync-filelist.bat fr.bat frpost.bat frpost-helper.pl sync-filelist-helper.pl checktemp.bat settmp.bat fix-window-title.bat imageindex.btm setwidth.bat hilight.bat extract-all-wavs.bat extract-all-WAVs-from-video-files.bat extract-all-WAVs-from-audio-files.bat extract-wav.bat extract-cover_art-from-first-found-audio-file.bat extract-cover_art-from-first-found-mp3.bat extract-jpg.bat extract-mp3.bat generate-and-play-random-midi.bat generate_and_play_random_midi.py reddit-user-download.bat editGrep.bat mp42gif.bat mv.bat head.bat kill.bat label.bat more.bat validate-file-extension.bat split-mp3-by-inputted-chapter-info.bat split-mp3-by-inputted-chapter-info-helper.py pause-for-x-seconds.bat fix_wrong_image_extensions.py sleep.bat strip-blank-lines.bat add-art-to-mp3.bat add-art-to-song.bat ydl.bat ingest_youtube_album.py cover_embedder.py delete-zero-byte-files.bat exit-maybe.bat whisper-faster.bat generate-audio-transcripts-for-files-with-openlrc.py get-winamp-state.bat dice.bat d20.bat audio-countdown-noise.bat avg.bat average.py make-image-square.bat make-video-from-audio-and-image.bat crop-center-square-of-image.bat expand-image-to-square.bat age.bat display-time-elapsed.bat rn-latest-for-youtube-dl.bat rn-latest.bat rn.bat auto-clean.bat fix-google-photo-filenames.bat ensure-directories-exist.bat research-this-dir-on-discogs.bat research-this-dir-on-wikipedia.bat allfiles.bat auto-process.bat del-WAVs-if-mp3s-or-flacs-exist.bat del-WAVs-if-mp3s-exist.bat delete-WAVs-if-MP3s-exist.bat display-flac-tags.bat display-mp3-tags.bat display-bitrate.bat find-folder-that-meets-conditions.bat grab.bat put.bat handles.bat handles-post.pl normalize-all-wavs.bat qd.bat yyyymmddhhmmss.bat yyyymmddhhmm.bat yyyymmddclip.bat yyyymmdd.bat plot-generalized-graph---edit-data.bat  plot-generalized-graph---enter-new-data.bat plot-generalized-graph---plot-graph.bat rebuild_Icon_Cache.bat rotate-video.bat sizes.bat counts.bat counts-helper.bat create-generic-sizes-and-counts-report.bat start-nonelevated.bat alarm-beep.bat wav2mp3.bat allbmp2jpg.bat alljpg2bmp.bat allmp42wav.bat allpng2jpg500.bat alltif2jpg.bat flv2avi.bat join-videos.bat mkv2avi.bat mov2avi.bat mp42gif.bat mp42wav.bat mpc2wav.bat png2jpg500.bat py2exe.bat py2exe-create-spec-file.bat py.spec2exe.bat wget32.bat hstart.bat tail.bat zip-all-exes.bat zip.bat zip-file.bat zip-folder.bat zip-old.bat zip-all-folders.bat zip-all-subfolders.bat unzip-gracefully.bat unzip-all.bat monitor-to-react-after-program-closes.bat usb-remove-safely.bat drives.bat unmap-drives.bat strip-video-rotation-metadata.bat strip-ansi.pl stop-windows-update-reboot-nag.bat sort-by-human-readable-size.pl sort-by-line-length.pl list-exif-dates.bat exiflist.bat restart-tcpip-stack.bat restart-cpu-meter.bat remove-trailing-spaces.pl lock-computer.bat google.bat okgoogle.bat speak.bat find-first-filename-of-extension.bat symlink.bat create-symlinks.bat create-symlinks-by_Letter_only.bat connections-monitor.bat collapse-all-directories.bat clear-buffered-keystrokes.bat grant-me-access-to-all-files.bat chown.bat backup-to-dvds.bat backup-to-bdrs.bat backup-to-cds.bat backup-thing.bat convert-16bit-or-32bit-legacy-executable-to-64bit-exe.bat exitafter.bat add-m3u-to-winamp-playlist.bat del-FLACs-if-mp3s-exist.bat flac2wav.bat allflac2mp3.bat allwav2mp3.bat *.AHK fix-evillyrics-window-size-and-position.bat fix-lastfm-window-size-and-position.bat fix-minilyrics-window-size-and-position.bat fix-music-window-sizes-and-positions.bat load-window-positions.bat restore-window-positions.bat save-window-positions.bat commit-and-push.bat new-computer.btm new-computer.ps1 wake-computers.bat new-harddrive.bat prompt-sound.bat beep.bat speak-in-every-voice.bat audit-music-files.py display-connections.bat display-cuda-version.bat display-current-month.pl display-emojis-in-environment.bat display-exif-dates.bat exiflist.bat display-last-month.pl display_mp3_comment_with_eyed3_library_proof_of_concept_does_not_work_well.py display-this-month.pl cd.bat display-video-length.bat display-video-lengths.bat dvl.bat display-window-names.bat windowlist.bat dvl.bat rename_images_to_incorporate_folder_name.py cover_downloader.py set-all-screens-to-black.py chatgpt-query.py color-cycle-by-ansi-proof_of_concept.py convert_midi_to_wav_with_soundfont.py cls.bat facebook_photo_dump_renamer_looks_at_json_for_filedates_then_finds_files_and_renames_images_with_those_dates.py fix_taskbar_hidden_by_ctypes_call.py fix_unicode_filenames_every_char.py generate_midi_randomly.py get_lyrics_from_audio_file_via_whisperAI.py ingest_ics.py list_dependencies_of_CLI_script.py list_scripts_to_publish_and_create_script_database.py mtsend.py pickle_view.py play_wav_file.py pyclouds.py random_color_each_line.py return-a-0.py return-a-1.py show_current_pallete_prototype.py tock.py view_pickle.py wedding_party.py deltree.bat display-bluetooth-battery-levels.ps1 spl.bat splx.bat splh.bat splhx.bat splv.bat splvx.bat split-window-to-run-command-then-exit-after.bat split-windows-terminal-screen.ahk split-windows-terminal-screen-vertical.ahk dls.bat cfml.bat
        set SECONDARY_BAT_FILES_2=cat.bat du.bat diff.bat python.bat say.bat tee.bat window.bat wget.bat touch-alias.bat realias.bat hilight.bat hilight-by-computer-name.bat hilite-by-computer-name.bat mydrives.bat display-drives-by-computer.bat colorize-by-computer-name.bat display-drive-mapping.bat calibrate-monitor.bat delete-duplicate-files-including-subfolder-duplicates.bat delete-duplicate-files-in-each-subfolder-but-not-across-current-folder.bat fast_cat.bat move-current-TCC-window-to-top-left-screen.bat randfile.bat fixclip.bat clip.bat clipboard.bat cl.bat yyyymmdd(dow).bat wcclip.bat start-everything.bat chrome.bat opera.bat fml.bat autohotkey.bat validate-ahk.bat AutoHotKey-autoexec.bat autoexec.ahk create-all-drive-shares-(for-new-installations).bat install-autoexec-launcher-to-startup.bat insert-before-each-line.pl insert-after-each-line.pl debugEcho.bat edit-currently-playing-attrib.bat edit-currently-playing-attrib-helper.pl ec.bat get-current-song-playing.pl get-currently-playing-tracknum-from-wawi-index_html.pl nextdir.bat nd.bat previousdir.bat prevdir.bat pd.bat go-to-next-directory-generator.pl grab-helper.pl image-index.bat imageindex.bat imageindex.btm imageindex-quick.bat html_viewer.bat firefox.bat ie.bat left-center-right.pl makethumbnail.pl lowercase.pl  numbers.pl prevent-duplicate-lines.pl randomize-file.pl remove-trailing-spaces.pl reverse.pl select-random-lines-from.pl sizedir.pl trimdir.pl trimext.pl trimextonly.pl trimfile.pl uppercase.pl  urldecode.pl urlencode.pl winamp-status.pl winamp-status-from-file.pl uniq-relaxed.pl convert-each-line-to-a-dot.pl backup-important-files.bat backup-important-folders.bat rookie-pcvr.bat assimilate-rookie-folders.bat process-rookie-folders.bat git-rm.bat askYN.bat test-askyn.bat test-errorlevel-catcher.bat mount-iso.bat scream.bat all-ready-drives.bat preprocess-music-batch.bat dep.bat deprecate.bat deprecated.bat deprecate-all.bat dep-all.bat dep-MP3s-if-FLACs-exist.bat DataExecutionPrevention-turn-on.bat DataExecutionPrevention-turn-off.bat dep-on.bat dep-off.bat undep.bat detect-command-line-container.bat an.bat autoname.bat set-drive-related-environment-variables.bat setDrive.bat set-drive.bat setLabel.bat set-label.bat isRunning.bat isrunning-helper.bat isRunning-fast.bat disable-windows-key.bat winkill.bat google.bat research-this-dir-on-discogs.bat research-this-dir-on-wikipedia.bat autoprocess.bat display-mp3-tags.bat display-mp3-artists.bat divider.bat display-horizontal-divider.bat turn-off-file-redirection.bat turn-on-file-redirection.bat turn-nested-variable-expansion-off.bat turn-nested-variable-expansion-on.bat turn-off-command-separator.bat turn-on-command-separator.bat make-zero-byte-file-named.bat mcd.bat mcdnow.bat now.bat yyyymmdd.bat yyyymmdd(dow).bat yyyymmddhhmmss.bat yyyymmdddow.bat yyyymmddclip.bat mmddhhmmss.bat test-cd.bat numfiles.bat rd-alias.bat cd-alias.bat wake-all-drives-helper.bat wake-all-drives.bat sync-perl-libraries.bat sync-perl-libraries-to-dropbox.bat sync-perlsitelib-to-dropbox.bat exit-after-command.bat exit-after.bat exitafter.bat sync-perl.bat sync-python.bat sync-python-personal-libaries-to-dropbox.bat sync-python-libraries-to-dropbox.bat display-free-space.bat check-if-asking-for-usage.bat copy.bat copy-alias.bat pause-alias.bat dump-environment-to-tmpfile.bat display-message_type_environment-variables-and-corresponding-ansi-color-environment-variables.bat gather-message-types-into-pretty-environment-variable.bat install-common-programs-with-winget-helper.cmd check-for-invalid-audio-files.bat restart-winamp.bat winamp-restart.bat winamp-close-gracefully.bat winamp-start.bat winamp.bat set-winamp-constants.bat save-window-positions.bat restore-window-positions.bat fix-minilyrics-window-size-and-position.bat fix-winamp.bat MiniLyrics.bat start-MiniLyrics.bat stop-minilyrics.bat killIfRunning.bat ensure-drive-is-mapped.bat create-these_m3u-playlists.bat mp3index.bat generate-audio-playlists.bat generate-filelists-by-attribute.pl generate-filelists-by-attribute-audio.ini  generate-filelists-by-attribute-images-and-video-WWW.ini generate-filelists-by-attribute-video.ini mchk.bat music-search.bat search-music.bat wcpretty.bat wcnice.bat wcheader.bat helper-end.bat index-mp3.bat index-mp3-helper.bat celebrate.bat new-harddrive.bat new-computer.ps1 hosts.bat hosts-supplimental.txt allcomputers.bat allcomputersexceptself.bat validate-all-perl-files.bat create-all-drive-shares-(for-new-installations).bat install-common-programs-with-winget.bat install-common-programs-with-winget.lst setup-perl-junctions-on-new-computer.bat make-directory-matching-drive-label-on-every-drive.bat  make-directory-matching-drive-label.bat  ftphome.bat new-harddrive.bat StripAnsi.dll StripAnsi-x86.dll StripAnsi.txt audio-batch-processing---encode-everything-and-remove-redundant-WAVs.bat del-WAVs-if-mp3s-or-flacs-exist.bat preprocess-audio-tagging-batch.bat remove-art-from-flac.bat add-art-to-flac.bat add-art-to-flac-helper.bat rar.bat collapse-all-subfolders-into-current-folder.bat ydm.bat dym.bat download-youtube-music.bat  download-youtube-video-with-chapters-as-an-mp3-album.bat download-youtube-album.bat set-task.bat delete-largest-file.bat openimage.bat get-image-dimensions.bat warning_soft.bat set-current_playing_song.bat get-current-song-playing.pl set-nicetime.bat set-nice_time.bat set-automatic-login-to-windows-OFF.bat set-automatic-login-to-windows-ON.bat remove-commas-from-filenames.bat drastically-shorten-and-standardize-filenames.bat remove-pluses-from-filenames.bat Snipping-Tool.bat snip.bat sn.bat lowercase-all-filenames.bat remove-filename-characters-invalid-for-xbox360.bat remove-percents-from-filenames.bat validate-is-number.bat battery.bat batteries.bat bluetooth-batteries.bat bluetooth.bat convert-all-MOV-to-AVI.bat mov2avi.bat convert-all-video-to-MKV.bat convert-to-MKV.bat convert-to-AVI.bat play-these.bat switch-winamp-to-playlist.bat play-m3u-with-winamp.bat launch-monitor-to-react-after-program-closes.bat helper-start.btm winamp-randomize-playlist.bat randomize.bat car.bat nocar.bat bring-back-focus.bat bring-focus-back.bat wgetquiet.bat play.bat paus.btm pause.btm winamp-pause.bat unpause.bat winamp-unpause.bat winamp-play.bat play.bat stop.bat winamp-stop.bat play-m3u-with-VLC.bat playlist.bat winamp-next.bat next.bat prev.bat winamp-prev.bat remap.pl convert-slashes-to-backslashes.pl convert-slashes-to-backslashes.bat convert-16bit-or-32bit-legacy-executable-to-64bit-exe.bat convert-all-TS-to-MP4.bat convert-each-line-to-a-randomly-colored-dot.pl convert-each-line-to-a-dot.pl convert-id3-to-filenameregex.pl convert-newlines-to-spaces.pl convert-to-mp4.bat convert-to-mp4-h264.bat convert-webm-to-mp4.bat load-plugins.bat load-TCC-plugins.bat backup-game-saves.bat backup-save-games.bat backup-RockSmith.bat backup-Rogue_Legacy_2.bat backup-Xenia.bat val-env-var.bat go-to-next-directory-generator.pl nd.bat pd.bat make-text-double-height.bat make-text-double-height-helper.pl calmon.bat calendar-monitor.bat calendar-monitor-helper.bat restart-chrome.bat chrome.bat pf.bat programfiles.bat programfilesx86.bat install-program-with-winget.bat install-program.bat  install-winget.ps1 install-winget.bat publish.bat publish-bat-updates-to-github.bat insert-foldername-into-end-of-filenames.bat generate_thesem3u_and_allm3u_playlists_in_folder.py sp.bat dns-display.bat display-dns.bat tcc-in-console-window.bat where.bat display-mp3-lengths.bat display-mp3-length.bat cygecho.bat reset-ansi.bat reset.ansi tock.bat color-cycle-background.ansi color-cycle-background-briefly.bat generate_color_cycle_background_ansi.py remove-blank-lines.bat display-song-lengths.bat lengths.bat process-filelist-to-prevent-consecutive-entries-from-same-folder.bat reorder_playlist.py renumber-all-music-files-(to-randomize-usb-sticks).bat  album-art.bat album-art-tool-for-mp3Tag.bat album-art-tool-for-mp3Tag-beforeDash.bat clean.bat clean-dbcu.bat fix-google-photo-filenames.bat validate-extension.bat
        set SECONDARY_BAT_FILES_3=clean-rocksmith-dlc-dir.bat display-size-of-current-folder-tree.bat strip-html.pl autoexec-common.btm do-in-each-folder.bat do-in-each-directory.bat insert-before-each-filename.bat insert-after-each-filename.bat run-piped-input-as-bat.bat run-clipboard-as-bat.bat run-first-image-file-in-directory.bat run-first-file-in-folder.bat run-first-file-in-directory.bat run-first-file-in-dir.bat run-com-file.bat run-all-backups.bat run-cmd-file.bat backup-to-every-drive.bat backup.bat backup-utorrent.bat dist.bat distribute-bat-files-to-every-drive.bat bat.bat go-to-bat-file-folder.bat sync-dropbox.bat sync-bat-to-dropbox.bat sync-util-to-dropbox.bat sync-TCC-to-dropbox.bat sync-pub_journal-to-dropbox.bat sync-perlsitelib-to-dropbox.bat sync-winamp-playlists-to-dropbox.bat clean-dropbox.bat check-that-we-are-running-on-the-master-machine.bat dropbox-offload.bat startafter1secondpausewithexitafter.bat backup-stuff.bat backups.bat set-all_colors.bat roll-logs.bat roll-log-madvr.bat roll-lastfm-log.bat start-lastfm.bat lastfm-start.bat programfilesx86.bat display-open-file-handles.bat update-cygwin.bat freemon.bat free-space-monitor.bat free-space.bat free-up-harddrive-space.bat clairevironment-install.bat midirandia.midi midirandia.wav note-frequencies.dat note-frequencies.txt completion.bat set-prompt.bat warning_less.bat normal.bat strings.bat winamp_monitor.py winamp-close-gracefully.bat make-file-list.bat make-filelist.bat makefilelist.bat test-ansi-background-color-bug.bat jpg2png.bat git-fix-remote-repository.bat git-pull.bat deprecate-files-in-other-folder-if-they-have-the-same-name-as-files-in-this-folder.bat cuda-clear-cache.bat cuda-version.bat start-minimized.bat startafter1secondpause.bat start-windows-update-services.bat start-tagging-images.bat makeattrib.bat make-attrib_lst.bat start-milkdrop-fullscreen.bat start-elevated.bat start-displayFusion.bat stop-windows-11-automatic-repair-mode.bat stop-milkdrop.bat milkdrop3.bat milkdrop.bat restart.bat restart-explorer.bat restart-winamp-visualizer.bat restart-taskbar-autohide.bat restart-ttrgb.bat TTRGB.bat restart-process.bat restart-minilyrics.bat restart-lastfm.bat restart-ip-stack-(requires-reboot).bat restart-displayfusion.bat restore-window.bat window-restore.bat maximize.bat window-maximize.bat set-ansi.bat set-escape-character-and-command-separator-character.bat ansi-reset.bat functions-help.bat help-functions.bat validate-functions.bat validate-function.bat functions.bat validate-is-function.bat validate-env-vars.bat random-cursor-shape.bat random-cursor-color.bat random-cursor.bat randcursor.bat cursor-Carolyn.bat cursor-Claire.bat set-cursor.bat convert-each-line-to-a-randomly-colored-dot.py remove-x-characters-from-beginning-of-filenames.bat edit-windows-terminal-settings.bat display-tab-stops.bat reset-tab-stops.bat ansi-references.bat random-infinite-dots.bat randdots.bat randots.bat convert-com-to-64bit-exe.bat set-insert-on.bat restart-ahk.bat locked-message.bat lm.bat display-free-space-as-locked-message.bat unlock-margins.bat unlock.bat play-wav-file.bat dir-by-access-date.bat dir-by-creation-date.bat dir-by-modification-date.bat eject-usb.bat eject.bat unmap-drive.bat see-which-songs-a-band-is-currently-playing-live.bat search-for-steam_etc-coupons-for-games.bat app-volume-and-device-preferences.bat app-volume-and-device-preferences.lnk app-volume-and-device-preferences.ico volume.bat snd.bat pending-moves.bat pendingmoves.bat pending_moves.bat pendmoves.bat app-volume-and-device-preferences-install-button-to-taskbar.bat app-volume-and-device-preferences-hotkey.bat display-all-@CHARs.bat symlink-create-automatic-symlinks.bat wait.bat remove-currently-playing-song-from-playlist.bat remove-currently-playing-song-from-winamp-playlist.bat delete-track-from-currently-playing-playlist.bat swap.bat  determine-currently-playing-playlist-tracknumber.bat top-banner.bat top-message.bat top-msg.bat header.bat hdr.bat fix-MiniLyrics.bat alarmbeep.bat sync-music.btm sync-pictures.bat sync-cameras.bat sync-mp3-playlists-to-location-helper.pl sync-mp3-playlists-to-location.bat sync-perl-libraries-to-every-computer.bat sync-photos.bat sync-pics.bat sync-pictures-to-drive-setup.bat sync-playlist.bat sync-python-libraries.bat sync-python-libraries-to-every-computer.bat sync-winamp-program-to-burn-workflow.bat sync-mp3-playlists-to-carolyn's-mp3player-helper.pl sync-mp3-playlists-to-carolyn's-mp3player.bat validate-important-mp3-player-playlists.bat validate-important-playlists.bat validate-filelist.bat validate-filelist.pl cut-to-width.bat rename-file-named-nul.cmd get-meat-from-mp3-filename.pl settmpfile.bat save-clipboard-to-temp-file.bat convert-setlist-to-playlist-m3u-file.bat create-all_m3u-playlists.bat create-directory-and-recursive-playlists.bat generate-video-playlists.bat index-video-playlists.bat go-to-video-repository.bat make-CD-ISO-based-on-playlists.bat ramdrive.bat ramdisk.bat unmount-ramdisk.bat unmount-ramdrive.bat make-playlist.bat randomize-playlist.bat winamp-playlist-randomize.bat randomize-winamp-playlist.bat reload-playlist.bat reload-playlist-and-play.bat checkpassword.bat sayspeak.bat speak.bat turn-monitor-off.bat moff.bat util.bat assimilate.bat bedtime.btm asleep.bat sleeping.bat awake.bat morning.bat start-utorrent.bat utorrent.bat utorrent-start.bat div.bat coolbigecho.bat cool-header.bat ydl-upgrade.bat checkeditor.bat editor-slow.bat edit-filenames-matching-regex.bat grepEdit.bat tracking-number-unknown.bat unknown-tracking.bat ups-tracking.bat usps-tracking.bat fedex-tracking.bat package-tracking.bat unknown-tracking.bat unknown-shipper-tracking.bat kill-some-annoying-processes.bat tweak.bat set-background-picture-for-johnsbackgroundswitcher.bat slideshow.bat irfanview.bat start-girder.bat girder.bat mv-without-explorer-running.bat x10.bat blacklights-on.bat blacklights-off.bat lights-on.bat lights-off.bat cancel-execution-if-on-music-server.bat metronome.bat editplus.bat get-command-line.bat detect-command-line.bat checkmappings-daemon.bat AI-song-identify.bat identify-song-by-AI.bat image-search.bat image-search-anysize.bat image-search-large.bat image-search-medium.bat run-eaa-in-appropriate-subfolders.bat eaa-if-appropriate-for-workflow.bat eaa.bat extract-cover_art-from-first-found-audio-file.bat unlock-header.bat unlock-top.bat unique-lines.pl  edit-currently-playing-attrib-with-automark.bat rn-currently-playing-song.bat insert-before-each-line.py cl.bat google.pl  reset-cursor.bat cursor-reset.bat print-with-columns.bat print_with_columns.py newspaper.bat cursor-common.bat show-screen-font-information-and-character-aspect-ratio.py escape.txt del-if-exists.bat eset.bat eset-alias.bat see-latest-version-of-BAT-on-github.bat github.bat sortclip.bat sort-clipboard.bat display-tags.bat list-mp3-tags.bat display-lyrics.bat show-tags.bat show-lyrics.bat check-a-playlist-for-missing-subtitle-files.bat whichdrive.bat mv-alias.bat header-and-bigecho.bat  enqueue-file-into-winamp-playlist.bat enqueue.bat cancelll.bat ripGrep.bat  validate-is-extension.bat who.bat half-emoji-dance.bat half-emoji-dancers.bat restart-AutoHotKey.bat start-windows-installer-service.bat env.bat env.pl env-internal.bat env-internal-helper.bat 
        set SECONDARY_BAT_FILES_4=display-environment-variables-that-are-harddrives.bat winamp-add.bat  display-comic-book.bat cdisplay.bat bigecho-cool-cursive.bat edit-all-BAT-files-that-do-not-contain-a-string.bat PhraseExpress-Claire.csv turn-ansi-off.bat turn-ansi-on.bat ansi-off.bat ansi-on.bat download-4WT-plugin.bat ascii.bat 4wt.dll 4wt.txt emoji-search-online.bat unicode-character-search.bat unicode-search-online.bat emoji-character-search.bat defragment-files-in-this-folder-tree.bat pending-file-moves.bat display-pending-file-moves.bat backup-clairecjs_utils.bat backup-perl-libraries.bat firewall-enable-PsExec-traffic.bat 


        rem Ones specific to AI transcription system:
        set SECONDARY_BAT_FILES_5=add-ADS-tag-to-file.bat approve-lyric-file.bat approve-lyrics.bat approve-subtitle-file.bat approve-subtitles.bat change-single-quotes-to-double-apostrophes.py check-for-missing-karaoke.bat check-for-missing-lyrics.bat check-playlist-for-missing-lyrics.bat check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py clean-up-AI-transcription-trash-files-everywhere.bat clean-up-AI-transcription-trash-files-here.bat clean-up-AI-transcription-trash-files.bat cmkh.bat cmlf.bat cpfml.bat cpmlf.bat create-lrc-file-for-currently-playing-song.bat create-lrc-from-file.bat create-missing-karaoke-files.bat create-srt-file-for-currently-playing-song.bat create-srt-for-soundclip.bat create-srt-from-file.bat create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat create-srt.bat create-the-missing-karaokes-here.bat disapprove-lyric-file.bat disapprove-lyrics.bat disapprove-subtitle-file.bat disapprove-subtitles.bat display-ADS-tag-from-file.bat display-lyric-status-for-file.bat display-lyric-status.bat downloaded-lyrics-postprocesser.bat eccsrt2lrc2clip.bat get-karaoke.bat get-lyrics-for-all-songs-in-this-folder.bat get-lyrics-for-playlist.bat get-lyrics-from-song.bat get-lyrics-with-lyricsgenius-json-processor.pl get-lyrics-with-LyricsGenius.bat get-lyrics.bat get-missing-karaoke.bat get-missing-lyrics-here.bat get-missing-lyrics.bat go-to-currently-playing-song-dir.bat google.py insert-after-each-line.py lrc.bat re-srt.bat read-ADS-tag-from-file.bat redo-last-SRT-creation.bat redo-last-srt.bat redo-srt.bat remove-ADS-tag-from-file.bat remove-period-at-ends-of-lines.pl resrt.bat review-all-SRTs.bat review-all-TXTs.bat review-file.bat review-files.bat review-karaokes.bat review-LRCs.bat review-lyrics.bat review-srt.bat review-SRTs.bat review-subtitles.bat review-txt.bat review-TXTs.bat show-lyric-status.bat show-lyric-status.bat srt2lrc.py srt2txt.py srtthis.bat unapprove-lyric-file.bat unapprove-lyric-file.bat unapprove-lyrics.bat unapprove-subtitle-file.bat unapprove-subtitles.bat approve-lyriclessness.bat disapprove-lyriclessness.bat unapprove-lyriclessness.bat approve-lyriclessness-for-file.bat disapprove-lyriclessness-for-file.bat unapprove-lyriclessness-for-file.bat get-lyriclessness-status.bat display-lyriclessness-status.bat display-lyriclessness-status-for-file.bat
        
        set SECONDARY_BAT_FILES_6=
        set SECONDARY_BAT_FILES_7=


        rem 2022/11/23: trying to deprecate this one: start.bat 

        rem Only add files that live in C:\UTIL\ to this list:        
        set SECONDARY_UTIL_FILES=mencoder.exe wget.exe wget32.exe focus-monitor.exe handle.exe hstart.exe hstart64.exe normalize.exe RemoveDrive.exe exiflist.exe speak.exe wsay.exe ansi2html.exe ansi2html.txt pizza-per-square-inch-calculator.exe wake-on-lan.exe windowhide.exe cat_fast.exe winkill.exe winkillhook.dll LaunchKey.exe LaunchKey.cnt LaunchKey.hlp LaunchKey.txt girder-internet-event-client.exe msdos-player.exe taskbar-autohide.exe msdos.exe junction.exe pendmoves.exe imdisk.exe nircmd.exe x10cmd.exe grep32.exe LRCget.exe rg.exe gawk.exe Enqueueee-make.bat Enqueueee.cpp Enqueueee.cpp.original.txt enqueueee.exe Enqueueee.cpp-uses-winamp.h.txt winamp.h winamp.h-is-used-by-enqueueee.txt enqueueee2024.zip sort.exe uniq.exe
        rem DECIDED AGAINST: metaflac.exe metamp3.exe metamp3.txt  lyricy.exe


rem Parameters:
        :initialize_params
                set GO_STRAIGHT_TO_GIT=0
                set        SKIP_UPDATE=0
                set          DOCS_ONLY=0
                set             FASTER=0
        :check_params
                set PARAM_FOUND=0
                if "%1" eq "git"         (set PARAM_FOUND=1 %+ set GO_STRAIGHT_TO_GIT=1)                                       
                if "%1" eq "skip-update" (set PARAM_FOUND=1 %+ set        SKIP_UPDATE=1)                                       
                if "%1" eq "docs"        (set PARAM_FOUND=1 %+ set          DOCS_ONLY=1 %+ set FASTER=1)
                if   1  eq %PARAM_FOUND% (shift             %+ goto       :check_params)
                if "%1" ne ""            (call print-message error "don’t know what this %[1st] parameter of “%italics_on%%1%italics_off`%” is supposed to mean")

        rem DEBUG: echo [A]faster is %FASTER% , param_found is %PARAM_FOUND%, docs_only is %DOCS_ONLY% %+ pause


rem Only once per session, validate our environment & make sure we’re running this on the correct machine:
        iff %GITHUB_UPDATER_VALIDATED ne 1 then
                call validate-environment-variables MACHINENAME MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY italics_on italics_off PYTHON_OFFICIAL_SITELIB_CLAIRE 1st
                call validate-in-path               c:\bat\update-from-BAT-via-manifest copy-move-post.py fast_cat divider AskYN git.bat commit-and-push.bat error error.bat print-message.bat
                if "%MACHINENAME%" ne "%MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY%" (call error "This script is only meant to be run on our primary machine named “%italics_on%%MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY%%italics_on%”, but this machine is named “%italics_on%%MACHINENAME%%italics_on%”" %+ goto :END)
                set GITHUB_UPDATER_VALIDATED=1
        endiff




rem Make sure none of our files are set as read-only, so that we can successfully update from our source files:
        gosub setAttribs "-r"
        rem   setAttribs is right here:  
                        goto :end_of_subroutines
                                :setAttribs    [attrib_to_set]
                                        rem This subroutine also gets called when we are done, but with "+r" instead of "-r"
                                        call    less_important "Setting file attributes to %italics_on%%attrib_to_set%%italics_off%                        
                                        set     attrib_to_use=%@unquote[%attrib_to_set]
                                        attrib %attrib_to_use% %TARGET_2%\*.*      >nul
                                        attrib %attrib_to_use% %TARGET_1%\*.*      >nul     
                                        attrib %attrib_to_use% %TARGET_1%\docs\*.* >nul     
                                        attrib %attrib_to_use%            docs\*.* >nul
                                return
                        :end_of_subroutines

rem Manually-selected copies from locations other than C:\BAT\ ——— Step #1 ——— Define variables for each of the files/folders:
        rem TCC files needed for compatibiity: TODO add notes about these in docs?
                set          TCMD_DIR=c:\TCMD
                set          TCMD_INI=%TCMD_DIR%\tcmd.ini                             
                set      TCMD_ALIASES=%TCMD_DIR%\alias.lst                            
                set TCMD_START_SCRIPT=%TCMD_DIR%\tcstart.bat                          
        rem Programming [Python+Perl] libraries needed for compatibility:
                set    PERL_SITELIB_CLAIRE_ZIP=%PUBCL%\dev\Perl\Clio.zip
                set      PERL_SITELIB_FULL_ZIP=%PUBCL%\dev\Perl\perl-site-lib.zip        
                set       PYTHON_LIBRARIES_DIR=%PYTHON_OFFICIAL_SITELIB_CLAIRE%                
        rem Configuration files that might help with compatibility:
                rem Our Windows Terminal configuration:
                        rem WINDOWS_TERMINAL_SETTINGS should be set in environm.btm, but just in case, let’s try here:
                        iff not defined WINDOWS_TERMINAL_SETTINGS then
                                set WINDOWS_TERMINAL_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
                                call validate-environment-variable WINDOWS_TERMINAL_SETTINGS 
                        endiff                                                
        rem Deprecated: Our Girder configuratoin, which becomes less relevant as the years go by:                        
                set GIRDER_CONFIGURATION="c:\girder\claire's girder files\%MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY%.gml"                                
        rem Notes that we’d like to share for fun:
                set     WINAMP_SETUP_NOTES=%NOTES%\winamp-notes.txt
                set AUDIO_PROCESSING_NOTES=%NOTES%\audio-processing-batch-NOTES.txt                        
        rem Set vars for files & folders in subfolders that we want to publish:                
                set PRIMARY_AUTOEXEC_BAT=%BAT%\%MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY%\autoexec.btm
                set        COLORTOOL_EXE=%UTIL%\ColorTool\ColorTool.exe
                set      DIVIDERS_FOLDER=%BAT%\dividers
                set       SAMPLES_FOLDER=%BAT%\samples
                set          DOCS_FOLDER=%BAT%\docs
                    

rem Validate the above (and other) values that we will be using here:
        if 1 eq %DOCS_ONLY (
                set to_validate=DOCS_FOLDER
        ) else (                
                set to_validate=BAT UTIL PUBCL NOTES GIRDER_CONFIGURATION AUDIO_PROCESSING_NOTES PERL_SITELIB_CLAIRE_ZIP PERL_SITELIB_FULL_ZIP COLORTOOL_EXE PRIMARY_AUTOEXEC_BAT TCMD_ALIASES TCMD_INI TCMD_START_SCRIPT WINAMP_SETUP_NOTES WINDOWS_TERMINAL_SETTINGS DIVIDERS_FOLDER SAMPLES_FOLDER PYTHON_OFFICIAL_SITELIB_CLAIRE DOCS_FOLDER
        )           
        call validate-environment-variables %to_validate%

rem Manually-selected files from locations other than C:\BAT\ ——— Step #3 ——— Copy the files:
        rem Set our copy commands:
                set   COPY=*copy /u /q
                set COPY_S=*copy /u /q /s
        rem Adjustment for special modes:
                iff 1 eq %DOCS_ONLY then
                        goto :docs_only_goto_1
                endiff                        
        rem Files that don’t normally live in C:\BAT\ but which we copy there for distribution, to keep things simple:        
                %copy%  %TCMD_ALIASES%                %TARGET_MAIN%\alias.lst
                %copy%  %TCMD_INI%                    %TARGET_MAIN%\tcmd.ini
                %copy%  %GIRDER_CONFIGURATION%        %TARGET_MAIN%\girder.gml
                %copy%  %TCMD_START_SCRIPT%           %TARGET_MAIN%\tcstart.bat
                %copy%  %PRIMARY_AUTOEXEC_BAT%        %TARGET_MAIN%\autoexec.btm
                %copy%  %COLORTOOL_EXE%               %TARGET_MAIN%\ColorTool.exe
        rem Some things we want to copy into a different filename than the original filename:
                %copy%  %PERL_SITELIB_CLAIRE_ZIP%     %TARGET_MAIN%\perl-sitelib-Clio.zip
                %copy%  %WINAMP_SETUP_NOTES%          %TARGET_MAIN%\winamp-setup-notes.txt
                %copy%  %AUDIO_PROCESSING_NOTES%     "%TARGET_MAIN%\notes - audio processing.txt"
                %copy% "%WINDOWS_TERMINAL_SETTINGS%"  %TARGET_MAIN%\windows-terminal-settings.json-to-be-copied-into-WT-dir-at-own-risk.json
        rem Also, put this script (this one that you’re reading these words from right now!) into the target for completionism:
                %copy% %0 %TARGET_MAIN%                 
        rem Update programming libraries:                
                rem Update python libraries to the copy that lives in our BAT folder: both the ’living’ one, and the copy here:
                        %copy_S% /E %PYTHON_LIBRARIES_DIR%         c:\bat\clairecjs_utils
                        %copy_S% /E %PYTHON_LIBRARIES_DIR%  %TARGET_MAIN%\clairecjs_utils
                rem Update perl libraries:
                        %copy%  %PERL_SITELIB_FULL_ZIP%  %TARGET_MAIN%                
        rem Subfolders we want to publich will need to be explicitly added:
                rem Subfolders that need to be copied once:
                        %copy_S%  %DIVIDERS_FOLDER%  %TARGET_MAIN%\dividers
                        %copy_S%  %SAMPLES_FOLDER%   %TARGET_MAIN%\samples
                rem Subfolders that need to be copied twice:
                        :docs_only_goto_1
                        %copy_S%  %DOCS_FOLDER%  %TARGET_MAIN%\docs
                        %copy_S%  %DOCS_FOLDER%  %TARGET_MAIN%\..\docs
                        rem If this ever gets moved to anything but the last section here, we will have to have another iff-goto to skip over the rest





rem Update BAT files from live location to github-folder location:
        unset /q COMMIT_WITH_AUTOMATIC_REASON
        unset /q GIT_SKIP_COMMIT_REASON_EDIT
        iff 1 eq %SKIP_UPDATE .or. 1 eq %DOCS_ONLY then
                set comment=Skip it!
                set GIT_SKIP_COMMIT_REASON_EDIT=1
                set COMMIT_WITH_AUTOMATIC_REASON=1
        else
                call c:\bat\update-from-BAT-via-manifest %TARGET_MAIN% %*
        endiff


rem Update our copy of BAT-1 folder’s later-letters to our BAT-2 folder to get past GitHub’s 1000 1,000 file 
rem display limit so that bat files starting with Z can actually be browsed to:
        if 1 ne %last_git_was_null% (echo.)
        call less_important "Updating %italics_on%BAT-2%italics_off% from %italics_on%BAT-1%italics_off%..."
        echo.
        (((echo rayr|*copy /u /r /Ns %TARGET_MAIN%\[m-z]* %TARGET_2% ) |:u8 copy-move-post.py) |:u8 fast_cat)


rem Give a chance to stop here...
        echo.
        call divider
        if 1 eq %FASTER goto :git_add_done
        echo.
        call askYN "Continue with git add + commit + push?" yes %COMMIT_CONFIRMATION_WAIT_TIME%
        if %DO_IT eq 0 (goto :Skip_TheRest)

rem Make sure they’re all added —— any new extensions that we add to our project, need to be added here:
        :git_yes
        rem extensions that only appear in [a-l]*.*
                call git.bat add docs\* %TARGET_MAIN%\samples\* %TARGET_MAIN%\dividers\* %TARGET_MAIN%\*.hlp  %TARGET_MAIN%\*.cnt %TARGET_MAIN%\*.lst %TARGET_MAIN%\*.gml %TARGET_MAIN%\*.jpg %TARGET_MAIN%\*.png %TARGET_MAIN%\*.lnk  %TARGET_MAIN%\*.ico 
                
        rem extensions that appear in [m-z]*.*
                for %%tmpfolder in (%TARGET_MAIN% %TARGET_2%) do (
                        call git add %tmpFolder%\*.bat %tmpFolder%\*.csv LICENSE *.md .gitattributes .gitignore %tmpFolder%\*.exe %tmpFolder%\*.btm %tmpFolder%\*.pl  %tmpFolder%\*.py   %tmpFolder%\*.exe   %tmpFolder%\*.ahk %tmpFolder%\*.ini %tmpFolder%\*.zip %tmpFolder%\*.ansi %tmpFolder%\*.midi  %tmpFolder%\*.wav %tmpFolder%\*.dat %tmpFolder%\*.dll %tmpFolder%\*.json go-to-individual-BAT-files-on-GitHub.bat update-from-BAT-and-push-and-commit.bat
                )
                
        rem This secondary folder seems to be having troubles sometimes... Re-add just to be sure.
                call git.bat add %TARGET_2%\*.bat
        :git_add_done                

rem Make file readonly again:
        rem echo 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
        echo.
        gosub setAttribs "+r"
        
rem Commit and Push:
        echo.
        call divider
        echo.
        set  no_push_warning=1
        rem  commit-and-push.bat %* is a BAD call , do NOT pass %*
        call commit-and-push.bat 
        echo https://github.com/ClaireCJS/clairecjs_bat/tree/main/%TARGET%  >go-to-individual-BAT-files-on-GitHub.bat



rem Cleanup:
        rem Set files to be read-only so we don’t accidentally edit them in the wrong place:
                
        :Skip_TheRest
                unset /q SECONDARY_BAT_FILES
                unset /q SECONDARY_BAT_FILES_2
                unset /q SECONDARY_BAT_FILES_3
                unset /q SECONDARY_BAT_FILES_4
                rem unset /q SECONDARY_BAT_FILES_5
                unset /q SECONDARY_BAT_FILES_6
                unset /q SECONDARY_BAT_FILES_7
                unset /q SECONDARY_BAT_FILES_8
                unset /q SECONDARY_BAT_FILES_9
                unset /q SECONDARY_BAT_FILES_2
                unset /q SECONDARY_BAT_FILES_3
                unset /q SECONDARY_BAT_FILES_4
                unset /q SECONDARY_BAT_FILES_5   
        :END

rem echo %ansi_color_removal%👻 leaving %0 in %_CWD tha was called by %_PBATCHNAME%ansi_color_normal% %+ pause