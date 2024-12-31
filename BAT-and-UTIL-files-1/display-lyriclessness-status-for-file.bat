@Echo OFF

set  audio_file=%1
call validate-environment-variable audio_file "1ˢᵗ argument to “%0” must be an audio file to check the lyric%italics_on%lessness%italics_off% of"
call validate-is-extension %audio_file% %filemask_audio%
rem  display-lyric-status-for-file %audio_file% lyriclessness 🐐
call display-lyric-status-for-file %audio_file% lyriclessness

