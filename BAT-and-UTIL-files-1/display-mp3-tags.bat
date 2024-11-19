@on break cancel
@Echo OFF

if %VALIDATED_DISPLAYMP3TAGS ne 1 (call validate-in-path metamp3 ffprobe eyed3 sed)
set VALIDATED_DISPLAYMP3TAGS=1

set  DMP3PARAMS=%*
if "%DMP3PARAMS%" eq "*" (set DMP3PARAMS=*.mp3)


iff "*.mp3" eq "%DMP3PARAMS%" .or. "*" eq "%DMP3PARAMS%" then
        echo for %%tmpmp3 in (*.mp3) do echo gosub DisplayMp3Tags "%tmpmp3%"
else
        gosub DisplayMp3Tags %DMP3PARAMS%
endiff


goto :END
        rem —————————————————————————————————————————————————————————————————————————————————————————————————
                :DisplayMp3Tags [filename]        
                
                        iff 1 ne %DISPLAY_TAGS_PREFIX_NAME% then
                                metamp3 --info %filename%
                                ffprobe -i %DMP3PARAMS%
                                rem nope ffprobe -v quiet -print_format json -show_entries format_tags=lyrics %*
                                rem Yup:
                                call display-lyrics %DMP3PARAMS%
                        else
                               rem metamp3 does not utf pipe correctly or even |&| correctly, just use normal |:
                               (metamp3 --info %filename%        |    insert-before-each-line "%ansi_color_magenta%%@UNQUOTE[%1$]%faint_on%:metamp3%faint_off%:%ansi_color_normal% ") |:u8 fast_cat  |:u8 fast_cat         %+ rem                                 rem metamp3 does not utf pipe correctly or even |&| correctly, just use normal |
                               ffprobe -i %DMP3PARAMS%         |&|:u8 insert-before-each-line "%ansi_color_magenta%%@UNQUOTE[%1$]%faint_on%:ffprobe%faint_off%:%ansi_color_normal%" ) |:u8 fast_cat
                               call display-lyrics %DMP3PARAMS%
                        endiff
        
                return
        rem —————————————————————————————————————————————————————————————————————————————————————————————————
:END




