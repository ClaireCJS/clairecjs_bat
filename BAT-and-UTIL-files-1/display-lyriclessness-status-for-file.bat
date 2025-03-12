@loadbtm on
@Echo OFF

set  audio_file=%1
if not exist %1 call validate-environment-variable  audio_file "1ˢᵗ argument to “%0” must be an audio file [that exists] to check the lyric%italics_on%lessness%italics_off% of"
iff "1" != "%filemask_audio_validated%" then
        if not defined filemask_audio call validate-environment-variable  filemask_audio skip_validation_existence
        set filemask_audio_validated=1
endiff
call validate-is-extension         %audio_file% %filemask_audio%
rem  display-lyric-status-for-file %audio_file% lyriclessness 🐐
call display-lyric-status-for-file %audio_file% lyriclessness
 
