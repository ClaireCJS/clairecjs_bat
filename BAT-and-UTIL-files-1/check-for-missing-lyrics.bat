@Echo Off
 rem on break cancel

:USAGE: check-for-missing-lyrics ————————————————————— checks files in current folder, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics get ————————————————— checks files in current folder, and  gets all  the missing lyrics
:USAGE: check-for-missing-lyrics playlist.m3u get ———— checks files in   playlist.m3u, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics playlist.m3u ———————— checks files in   playlist.m3u, and  gets all  the missing lyrics


rem While we're here, do some cleanup: if exist *.json ((del /q *.json) >&nul)


rem Environment variable backups:
        if not defined NO                       set NO=%@CHAR[9940]%@CHAR[0]
        if not defined DASH                     set DASH=%@REPEAT[%@CHAR[9135],2]
        if not defined FILEMASK_AUDIO           set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        if not defined ANSI_COLOR_BRIGHT_PURPLE set ANSI_COLOR_BRIGHT_PURPLE=%@CHAR[27][38;2;255;0;255m
        if not defined ANSI_COLOR_MAGENTA       set ANSI_COLOR_MAGENTA=%@CHAR[27][38;2;170;0;85m

rem Validate environment:
        iff 1 ne %VALIDATED_CFMLB% then
                call validate-in-path set-tmpfile.bat get-lyrics.bat perl randomize-file.pl errorlevel.bat
                set  VALIDATED_CFMLB=1
        endiff                

rem If we were supplied a filename, process it as a list of files:
        set GET=0
        iff "%1" ne "" then
                set  FILELIST_TO_USE=%1
                set  FILELIST_MODE=1
                if "%1" eq "get" .or. "%2" eq "get" (set GET=1)
                if "%1" eq "get" (set FILELIST_TO_USE=)
                if "%1" eq "get" (set FILELIST_MODE=0)
                if "%1" ne "get" call validate-environment-variable FILELIST_TO_USE
        else                
                set  FILELIST_TO_USE=
                set  FILELIST_MODE=0
        endiff                
        
        rem DEBUG: echo filelist_to_use=%filelist_to_use% filelist_mode=%filelist_mode%
        
rem Go through each audio file, seeing if it lacks approved lyrics:
        set ANY_BAD=0
        call set-tmpfile
        iff 0 eq %FILELIST_MODE% then for %%AudioFile in (  %FILEMASK_AUDIO%  ) do (gosub process_file "%AudioFile%")
        else                          for %%AudioFile in (@"%FILELIST_TO_USE%") do (gosub process_file "%AudioFile")
        endiff
        
        iff 1 eq %ANY_BAD% then
                set TARGET_SCRIPT=get-the-missing-lyrics-here-temp.bat         %+ rem don't change w/o changing in clean-up-AI-transcription-trash-files and possibly in other places
                echo @Echo OFF                          >:u8 "%TARGET_SCRIPT"
                rem echo on break cancel               >>:u8 "%TARGET_SCRIPT"
                echo.                                  >>:u8 "%TARGET_SCRIPT"
                type %tmpfile |:u8 randomize-file.pl   >>:u8 "%TARGET_SCRIPT"
                
                iff 1 eq %GET then
                        rem echo type "%TARGET_SCRIPT%"
                        rem      type "%TARGET_SCRIPT%"
                        rem echo call "%TARGET_SCRIPT%"
                                 call "%TARGET_SCRIPT%"
                        call errorlevel
                        rem DEBUG: echo our_errorlevel is %our_errorlevel% 
                endiff
        endiff
        
        goto :process_file_end
             :process_file [AudioFile]
                     set textfile=%@UNQUOTE[%@name[%@UNQUOTE[%AudioFile%]].txt]
                     set BAD=1
                     iff exist "%textfile%" then 
                             set TXT_EXISTS=1
                             set coloring=%ansi_color_bright_green%
                             rem could do this: call add-ads-tag-to-file %LYRIC_FILE_TO_DISPLAY_STATUS_OF% lyrics read lyrics %+ rem sets RECEIVED_VALUE for return value
                             rem But let's just do it quick and direct:
                             rem echo set LYRIC_APPROVAL_VALUE=@ExecStr[TYPE  lt "%textfile%:lyrics"]
                             set LYRIC_APPROVAL_VALUE=%@ExecStr[TYPE <"%textfile%:lyrics" >&>nul]
                             iff "APPROVED" eq "%LYRIC_APPROVAL_VALUE%" then
                                     set coloring2=%coloring%
                                     set BAD=0
                             else                                
                                     set LYRIC_APPROVAL_VALUE=%ansi_color_bright_red%Nope%ansi_color_normal%
                                     set coloring2=%ansi_color_bright_red%
                             endiff
                     else                             
                             set TXT_EXISTS=0
                             set coloring=%ansi_color_bright_black%
                             set coloring2=%ansi_color_bright_black%
                             set LYRIC_APPROVAL_VALUE=%NO%
                     endiff              
                     iff 1 eq %BAD% then
                             set ANY_BAD=1
                             echo %EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%%@unquote[%AudioFile%] %+ rem currently has quotes
                             echo call get-lyrics "%@UNQUOTE[%AudioFile%]" >>"%tmpfile%"
                     endiff                        
                     rem DEBUG: echo %ansi_color_normal%* Checking %faint_on%%AudioFile%%faint_off% %@ansi_move_to_col[65] textfile=%faint_on%%textfile%%faint_off% %tab% %@ANSI_MOVE_TO_COL[125]%coloring%EXISTS=%txt_exists%%ansi_color_normal%   %coloring2%APPROVED=%LYRIC_APPROVAL_VALUE%
             return
        :process_file_end

rem Check for songs missing sidecar TXT files: abandoned way using sidecar-checking utility 
        rem call set-tmp-file
        rem echo.
        rem check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %FILELIST% *.txt GetLyricsFileWrite >%tmpfile
        rem for /f "tokens=1-9999" %co in (%TMPFILE%) do (gosub processline "%co%")
        rem goto :skip_sub
        rem         :processline [co_param]
        rem                 set co=%@UNQUOTE[%co_param%]
        rem                 iff 1 then
        rem                         set tf=%@name[%@unquote[%co%]].txt
        rem                         echo %star%%ansi_color_normal% audio file is: "%co%"
        rem                         if     exist %tf% echos %ansi_color_green%
        rem                         if not exist %tf% echos %ansi_color_red%
        rem                         echo     text file is: "%tf%"
        rem                 else
        rem                         echo %co%
        rem                 endiff                        
        rem         return       
        rem :skip_sub
        rem 
        rem |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING LYRICS %ANSI_RESET% %EMOJI_WARNING% %DASH% "

        