@Echo Off
 rem on break cancel

:DESCRIPTION: Checks for files that are missing *approved* lyric files.
:USAGE: check-for-missing-lyrics ————————————————————— checks files in current folder, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics get ————————————————— checks files in current folder, and  gets all  the missing lyrics
:USAGE: check-for-missing-lyrics playlist.m3u get ———— checks files in   playlist.m3u, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics playlist.m3u ———————— checks files in   playlist.m3u, and  gets all  the missing lyrics


rem Environment variable backups —— these should all already be defined already, but if not, define them here:
        rem Are our required filemasks set?
                iff 1 ne %FILEMASKS_HAVE_BEEN_SET then
                        if not defined FILEMASK_AUDIO           set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
                endiff
        rem Are our required emoji set?
                iff 1 ne %EMOJIS_HAVE_BEEN_SET% then
                        if not defined DASH                     set DASH=%@REPEAT[%@CHAR[9135],2]
                        if not defined NO                       set NO=%@CHAR[55357]%@CHAR[57003]
                endiff                
        rem Are our required ansi values set?
                iff 1 ne %ANSI_COLORS_HAVE_BEEN_SET% then
                        if not defined ANSI_COLOR_BRIGHT_PURPLE set ANSI_COLOR_BRIGHT_PURPLE=%@CHAR[27][38;2;255;0;255m
                        if not defined ANSI_COLOR_BRIGHT_RED    set ANSI_COLOR_BRIGHT_RED=%@CHAR[27][91m
                        if not defined            BRIGHT_RED    set            BRIGHT_RED=%@CHAR[27][91m
                        if not defined ANSI_COLOR_MAGENTA       set ANSI_COLOR_MAGENTA=%@CHAR[27][38;2;170;0;85m
                endiff

rem Validate environment once per session:
        iff 1 ne %VALIDATED_CFMLB% then
                call validate-in-path set-tmpfile get-lyrics perl randomize-file.pl errorlevel     %+ rem ensure everything we need exists, prior to proceeding
                set  VALIDATED_CFMLB=1                                                             %+ rem but set a flag so we only do this once per sessoin
        endiff                

rem If we were supplied a filename, process it as a list of files:                                 %+ rem This script can run in a couple different modes, so we need to deal with that
        set GET=0                                                                                  %+ rem Our default mode is GET=0, which means we will not be running the generated script afterward
        iff "%1" ne "" then                                                                        %+ rem If an argument was given, it should be "get", a filename, or a filename followed by "get"
                if "%1" eq "get" .or. "%2" eq "get" (set GET=1)                                    %+ rem if "get" was passed, we are actually going to run the script that this script generates. Adjust the flag for that               
                iff "%1" eq "get" then                                                             %+ rem if "get" was passed without a filename, we are actually NOT in filelist mode
                        if "%1" eq "get" (set FILELIST_MODE=0)                                     %+ rem if "get" was passed without a filename, we are actually NOT in filelist mode 
                        if "%1" eq "get" (set Filelist_to_Check_for_Missing_Lyrics_in=)            %+ rem if "get" was passed without a filename, we are actually NOT in filelist mode 
                else                                                                               %+ rem if "get" was passed  *WITH* a filename...
                        set  FILELIST_MODE=1                                                       %+ rem       ...set our operational mode flag appropriately...
                        set  Filelist_to_Check_for_Missing_Lyrics_in=%@UNQUOTE[%1]                 %+ rem       ...store the filename parameter for later...
                        call validate-environment-variable Filelist_to_Check_for_Missing_Lyrics_in %+ rem       ...and make sure the filename is a file that actually exists
                endiff                
        else                                                                                       %+ rem If run without parameters...
                set  Filelist_to_Check_for_Missing_Lyrics_in=                                      %+ rem       ...we are not using a fileist, so make sure that variable is empty
                set  FILELIST_MODE=0                                                               %+ rem       ...we are not using a fileist, so make sure the proper operational flag is set
        endiff                       
        rem DEBUG: echo Filelist_to_Check_for_Missing_Lyrics_in=%Filelist_to_Check_for_Missing_Lyrics_in% filelist_mode=%filelist_mode% %+ pause   %+ rem Debug
        
        
rem Go through each audio file, seeing if it lacks approved lyrics:
        set ANY_BAD=0                                                                              %+ rem Track if we found *any* bad files at all
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        iff 0 eq %FILELIST_MODE% then 
                for %%AudioFile in (  %FILEMASK_AUDIO%                          ) do (gosub process_file "%AudioFile%")    %+ rem If we are processing the current folder, look there for audio files, and add lines generating the missing lyrics (if any found) to %tmpFile
        else    
                rem Why am I not using my sidecar checker? This is what it’s made for: TODO: 🐐
                for %%AudioFile in (@"%Filelist_to_Check_for_Missing_Lyrics_in%") do (gosub process_file "%AudioFile%")    %+ rem If we are processing a playlist, look  through  it  for audio files, and add lines generating the missing lyrics (if any found) to %tmpFile
        endiff
        
        iff 1 eq %ANY_BAD% then                                                                    %+ rem We generate a script to find the missing ones, but if and only if some missing ("bad") ones were found
                set TARGET_SCRIPT=get-the-missing-lyrics-here-temp.bat                             %+ rem don’t change this!! Not w/o changing in clean-up-AI-transcription-trash-files and possibly in other places
                echo @Echo OFF                          >:u8 "%TARGET_SCRIPT"                      %+ rem get-missing-lyrics script: initialize: turn echo off
                rem echo on break cancel                 :u8 "%TARGET_SCRIPT"                      %+ rem get-missing-lyrics script: initialize: make ^C/^Break work better
                echo.                                  >>:u8 "%TARGET_SCRIPT"                      %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                type %tmpfile |:u8 randomize-file.pl   >>:u8 "%TARGET_SCRIPT"                      %+ rem get-missing-lyrics script: randomize the order of our script to eliminate alphabetical bias
                
                iff 1 eq %GET then                                                                 %+ rem If we have decided to auto-run the script, the let’s do that
                        rem echo type "%TARGET_SCRIPT%" ^ type "%TARGET_SCRIPT%"                   %+ rem Debug
                        rem echo call "%TARGET_SCRIPT%"                                            %+ rem Debug
                                 call "%TARGET_SCRIPT%"                                            %+ rem run the generated script
                        call errorlevel                                                            %+ rem check for errorlevel //rem DEBUG: echo our_errorlevel is %our_errorlevel% 
                endiff
        endiff
        
        
        
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
        
        goto :process_file_end                                                                     %+ rem Skip over subroutines
             :process_file [AudioFile]
                     if "%@LEFT[8,%@UNQUOTE[%AudioFile%]]" == "#EXTINF:" return
                     set textfile=%@UNQUOTE[%@name[%@UNQUOTE[%AudioFile%]].txt]                    %+ rem Create the filename of the lyric file that we will be looking for
                     set BAD=1                                                                     %+ rem Song is considered "bad" [does not have approved lyrics], until we find the accompanying files and mark it as "good"
                     iff exist "%textfile%" then                                                   %+ rem If the lyric file exists, we must check if it is approved
                             set TXT_EXISTS=1                                                      %+ rem If the lyric file exists, flag the situation as such
                             set coloring=%ansi_color_bright_green%                                %+ rem If the lyric file exists, draw debug info in green
                             set LYRIC_APPROVAL_VALUE=%@ExecStr[TYPE <"%textfile%:lyrics" >&>nul]  %+ rem If the lyric file exists, get it’s approval status
                             iff "APPROVED" eq "%LYRIC_APPROVAL_VALUE%" then                       %+ rem If the lyrics are approved...
                                     set coloring2=%coloring%                                      %+ rem    ...use the same success color for the text file
                                     set BAD=0                                                     %+ rem Mark it as "good" [having approved lyrics] by un-setting "bad"
                             else                                                                  %+ rem If the lyrics are NOT approved...
                                     set LYRIC_APPROVAL_VALUE=%bright_red%Nope%ansi_color_normal%  %+ rem    ...set a meaningful display value like "Nope"
                                     set coloring2=%ansi_color_bright_red%                         %+ rem    ...set the color to an alarming "angry" color
                             endiff
                     else                                                                          %+ rem If the lyrics don’t exist at all,
                             set TXT_EXISTS=0                                                      %+ rem    ...set a flag storing this fact
                             set coloring=%ansi_color_bright_black%
                             set coloring2=%ansi_color_bright_black%
                             set LYRIC_APPROVAL_VALUE=%NO%                                         %+ rem    ...set a meaningful display value like "🚫"
                     endiff              
                     iff 1 eq %BAD% then
                             set ANY_BAD=1
                             echo %EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%%@unquote[%AudioFile%] %+ rem currently has quotes
                             echo repeat 20 echo. `%`+ call get-lyrics "%@UNQUOTE[%AudioFile%]" >>:u8"%tmpfile%"
                     endiff                        
                     rem DEBUG: echo %ansi_color_normal%* Checking %faint_on%%AudioFile%%faint_off% %@ansi_move_to_col[65] textfile=%faint_on%%textfile%%faint_off% %tab% %@ANSI_MOVE_TO_COL[125]%coloring%EXISTS=%txt_exists%%ansi_color_normal%   %coloring2%APPROVED=%LYRIC_APPROVAL_VALUE%
             return
        :process_file_end

rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


:END
:Cleanup
        rem While we’re here, do some cleanup: if exist *.json ((del /q *.json) >&nul)
        