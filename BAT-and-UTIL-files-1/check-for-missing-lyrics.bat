@Echo Off
 rem on break cancel
setlocal
rem CONFIGURATION:
        set most_songs_from_playlist_to_process_at_a_time=10 %+ rem 🐐


:DESCRIPTION: Checks for files that are missing *approved* lyric files.
:USAGE: check-for-missing-lyrics ————————————————————— checks files in current folder, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics get ————————————————— checks files in current folder, and  gets all  the missing lyrics
:USAGE: check-for-missing-lyrics playlist.m3u get ———— checks files in   playlist.m3u, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics playlist.m3u ———————— checks files in   playlist.m3u, and  gets all  the missing lyrics


rem Environment variable backups —— these should all already be defined already, but if not, define them here:
        set original_title=%_TITLE
        rem Are our required filemasks set?
                iff 1 ne %FILEMASKS_HAVE_BEEN_SET then
                        if not defined FILEMASK_AUDIO           set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
                endiff
        rem Are our required emoji set?
                iff 1 ne %EMOJIS_HAVE_BEEN_SET% then
                        if not defined DASH                     set DASH=%@REPEAT[%@CHAR[9135],2]
                        if not defined NO                       set NO=%@CHAR[55357]%@CHAR[57003]
                        if not defined EMOJI_CHECK_MARK         set EMOJI_CHECK_MARK=%@CHAR[10004]%@CHAR[65039]
                endiff                
        rem Are our required ansi values set?
                iff 1 ne %ANSI_COLORS_HAVE_BEEN_SET% .and. 1 ne %validated_cfml_ansi% then
                        if not defined            BRIGHT_RED    set            BRIGHT_RED=%@CHAR[27][91m
                        if not defined ANSI_COLOR_BRIGHT_RED    set ANSI_COLOR_BRIGHT_RED=%@CHAR[27][91m
                        if not defined ANSI_COLOR_BRIGHT_PURPLE set ANSI_COLOR_BRIGHT_PURPLE=%@CHAR[27][38;2;255;0;255m
                        if not defined ANSI_COLOR_MAGENTA       set ANSI_COLOR_MAGENTA=%@CHAR[27][38;2;170;0;85m
                        if not defined BLINK_ON                 set BLINK_ON=%@CHAR[27][6m
                        set validated_cfml_ansi=1
                endiff

rem Validate environment once per session:
        iff 1 ne %VALIDATED_CFMLB% then
                call validate-in-path set-tmpfile get-lyrics perl randomize-file.pl errorlevel pause-for-x-seconds divider beep.bat set-tmp-file.bat
                set  VALIDATED_CFMLB=1                                                             
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
                        call less_important "Finding songs with missing lyrics in playlist: %italics_on%“%@NAME[%Filelist_to_Check_for_Missing_Lyrics_in%].%@EXT[%Filelist_to_Check_for_Missing_Lyrics_in%]%italics_off%”"
                endiff                
        else                                                                                       %+ rem If run without parameters...
                set  Filelist_to_Check_for_Missing_Lyrics_in=                                      %+ rem       ...we are not using a fileist, so make sure that variable is empty
                set  FILELIST_MODE=0                                                               %+ rem       ...we are not using a fileist, so make sure the proper operational flag is set
        endiff                       
        rem DEBUG: echo Filelist_to_Check_for_Missing_Lyrics_in=%Filelist_to_Check_for_Missing_Lyrics_in% filelist_mode=%filelist_mode% %+ pause   %+ rem Debug
        

rem Go through each audio file, seeing if it lacks approved lyrics:
        set ANY_BAD=0                                                                              %+ rem Track if we found *any* bad files at all
        set NUM_BAD=0
        set NUM_PROCESSED=0
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        set tmpfile2=%tmpfile%
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        set tmpfile_cfml_1=%tmpfile%
        
        rem echo tmpfile  is %tmpfile_cfml_1%%newline%tmpfile2 is %tmpfile2% %+ pause

        rem iff 0 eq %FILELIST_MODE% then 
        rem         for %%AudioFile in (  %FILEMASK_AUDIO%                          ) do (gosub process_file "%AudioFile%")    %+ rem If we are processing the current folder, look there for audio files, and add lines generating the missing lyrics (if any found) to %tmpfile_cfml_1
        rem else    
        rem         rem Why am I not using my sidecar checker? This is what it’s made for: TODO: 🐐
        rem         for %%AudioFile in (@"%Filelist_to_Check_for_Missing_Lyrics_in%") do (gosub process_file "%AudioFile%" %+ echo NUM_BAD=%NUM_BAD%)    %+ rem If we are processing a playlist, look  through  it  for audio files, and add lines generating the missing lyrics (if any found) to %tmpfile_cfml_1
        rem endiff


        iff 0 eq %FILELIST_MODE% then 
                set ENTITY_TO_USE=%FILEMASK_AUDIO%
                set LIMIT=9999
                if "%@FILES[%filemask_audio%]" !=  "" set LIMIT=%@FILES[%filemask_audio%]
        else    
                set LIMIT=%most_songs_from_playlist_to_process_at_a_time%
                randomize-file.pl  <"%Filelist_to_Check_for_Missing_Lyrics_in%" >%tmpfile2%
                set ENTITY_TO_USE=@"%tmpfile2%"
        endiff
        
        set remaining=%limit%

        rem If we are processing a playlist OR a wildcard set of files, look through it for audio files, 
        rem and add lines generating the missing lyrics (if any found) to %tmpfile_cfml_1:
        set limit_reached=0
        for %%AudioFile in (%ENTITY_TO_USE%) do (
                gosub process_file "%AudioFile%" 
                rem echo NUM_BAD=%NUM_BAD%
                if %NUM_BAD ge %LIMIT (
                        set limit_reached=1
                        leavefor 
                )
        )    
        call status-bar unlock
        echos %ansi_save_position%
        for %%offset in (-1) do (
               echos %@ansi_move[%@EVAL[%_rows-%offset],0]%ansi_erase_to_eol%
        )                
        echos %ansi_restore_position%
        
        
        
        if %ANY_BAD gt 0 repeat 5 echo.

        iff 1 eq %limit_reached then
                repeat 4 call beep.bat highest
                call bigecho "%ansi_color_warning_soft%%check%   Limit of: %italics_on%%blink_on%%@formatn[3.0,%LIMIT%]%blink_off%%%italics_off% files %ansi_color_success%reached%ansi_color_normal%"
        else                
                repeat 1 call beep.bat highest
        endiff
        
        iff %num_processed eq 0 then
                call warning "No files were processed here!"
        else
                set       fail_rate=%@EVAL[ %num_bad                  /%num_processed]
                set compliance_rate=%@EVAL[(%num_processed - %num_bad)/%num_processed]
                set  compliance_pct=%@EVAL[100*%compliance_rate]        
                set our_r=%@FLOOR[%@EVAL[      %fail_rate*255]]
                set our_g=%@FLOOR[%@EVAL[%compliance_rate*255]]
                set our_b=%@FLOOR[%@EVAL[%compliance_rate*255]]
                set formatted_percent=%@formatn[4.1,%compliance_pct%]
                if "%formatted_percent%" == "0.0" (
                        set clean_formatted_percent=0
                ) else (
                        set clean_formatted_percent=%formatted_percent%
                )
                call bigecho %ANSI_COLOR_BRIGHT_GREEN%%CHECK%  Processed: %italics_on%%@FORMATn[3.0,%NUM_PROCESSED%]%italics_off% songs 
                call bigecho %ANSI_COLOR_BRIGHT_GREEN%%CHECK%    Located: %ansi_color_red%%@FORMATn[3.0,%NUM_BAD%]%ansi_color_bright_green% songs needing lyric attention
                call bigecho %ANSI_COLOR_BRIGHT_GREEN%%CHECK% Compliance: %@ANSI_RGB[%our_r%,%our_g%,%our_b%]%@formatn[3.1,%clean_formatted_percent%]%cool_percent%
        endiff

        iff 1 eq %ANY_BAD% then                                                                    %+ rem We generate a script to find the missing ones, but if and only if some missing ("bad") ones were found
                set TARGET_SCRIPT=get-the-missing-lyrics-here-temp.bat                             %+ rem don’t change this!! Not w/o changing in clean-up-AI-transcription-trash-files and possibly in other places
                echo @Echo OFF                                  >:u8 "%TARGET_SCRIPT"              %+ rem get-missing-lyrics script: initialize: turn echo off
                rem echo on break cancel                         :u8 "%TARGET_SCRIPT"              %+ rem get-missing-lyrics script: initialize: make ^C/^Break work better
                echo.                                          >>:u8 "%TARGET_SCRIPT"              %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                type %tmpfile_cfml_1% |:u8 randomize-file.pl   >>:u8 "%TARGET_SCRIPT"              %+ rem get-missing-lyrics script: randomize the order of our script to eliminate alphabetical bias
                
                iff 1 eq %GET then                                                                 %+ rem If we have decided to auto-run the script, the let’s do that
                        rem title "Fetching lyrics!"
                        repeat 5 echo.
                        call divider
                        echo.
                        call divider
                        echos %@ANSI_MOVE_UP[2]
                        call pause-for-x-seconds 30 "%ansi_color_green%Going to find those missing lyrics now!%ansi_color_normal%%ansi_color_bright_Red%%blink_on%"
                        rem echo type "%TARGET_SCRIPT%" ^ type "%TARGET_SCRIPT%"                   %+ rem Debug
                        rem echo call "%TARGET_SCRIPT%"                                            %+ rem Debug
                                 call "%TARGET_SCRIPT%"                                            %+ rem run the generated script
                        call errorlevel                                                            %+ rem check for errorlevel //rem DEBUG: echo our_errorlevel is %our_errorlevel% 
                        title %original_title%
                endiff
        endiff
        
        
        
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
        
        goto :process_file_end                                                                     %+ rem Skip over subroutines
             :process_file [AudioFile]
                     set unquoted_audio_file=%@UNQUOTE[%AudioFile%]
                     if "%@LEFT[8,%unquoted_audio_file%]" == "#EXTINF:" return
                     iff not exist %AudioFile% then
                             echo %ansi_color_yellow% %EMOJI_CROSS_MARK% songfile doesn’t exist:        %faint_on%%@UNQUOTE[%AudioFile%]%faint_off%``                        
                     endiff
                     if "%@LEFT[4,%unquoted_audio_file%]" == "\\?\" set unquoted_audio_file=%@RIGHT[%@len[%unquoted_audio_file%-4],%unquoted_audio_file%]
                     set unquoted_audio_file_full=%@full[%unquoted_audio_file%]
                     set audio_file_path=%@path[%unquoted_audio_file_full%]
                     set audio_file_name=%@name[%unquoted_audio_file_full%]
                     set txtfile=%audio_file_path%%audio_file_name%.txt                            %+ rem Create the filename of the lyric file that we will be looking for
                     set srtfile=%audio_file_path%%audio_file_name%.srt                            %+ rem Create the filename of the  srt  file that may exist
                     set lrcfile=%audio_file_path%%audio_file_name%.lrc                            %+ rem Create the filename of the  lrc  file that may exist
                     set BAD=1                                                                     %+ rem Song is considered "bad" [does not have approved lyrics], until we find the accompanying files and mark it as "good"
                     rem iff 0 eq 1 then                                                               %+ rem debug
                     rem         echo 🌈 unquoted_audio_file     =%unquoted_audio_file%
                     rem         echo 🌈 unquoted_audio_file_full=%unquoted_audio_file_full%
                     rem         echo    audio_file_path         =%audio_file_path%
                     rem         echo    audio_file_name         =%audio_file_name%
                     rem         echo 🌈 txtfile=%txtfile%
                     rem         echo 🌈 lrcfile=%lrcfile%
                     rem         echo 🌈 srtfile=%srtfile%
                     rem endiff                             

                     rem iff exist "%srtfile%" then                                                    %+ rem If the  srt  file exists, skip this one 🦒 todo?: make this an option
                     rem         echo %ansi_color_blue%%check% karaoke already exists:        %srtfile%
                     rem         set BAD=0                                   
                     rem else                                                
                     rem         echo %ansi_color_magenta%%check% karaoke DOESN’T exist:         %srtfile%
                     rem endiff                                              
                     rem iff exist "%lrcfile%" then                                                    %+ rem If the  lrc  file exists, skip this one 🦒 todo?: make this an option
                     rem         echo %ansi_color_blue%%check% karaoke already exists:        %lrcfile% 
                     rem         set BAD=0                                   
                     rem else                                                
                     rem         echo %ansi_color_magenta%%check% karaoke DOESN’T exist:         %lrcfile% 
                     rem endiff                             
                     for %tmp_potential_subtitle_file in ("%srtfile%" "%lrcfile%") do (
                             if exist %tmp_potential_subtitle_file% (
                                     echo %ansi_color_cyan% %EMOJI_CHECK_MARK% karaoke  already exists:       %faint_on%%@UNQUOTE[%tmp_potential_subtitle_file%]%faint_off%``
                                     set BAD=0                                   
                             ) else (                          
                                     rem echo %ansi_color_magenta% %check% karaoke DOESN%[smart_apostrophe]T exist:         %@UNQUOTE[%tmp_potential_subtitle_file%]``
                             )                                            
                     )
                     
                     iff exist "%txtfile%" then                                                    %+ rem If the lyric file exists, we must check if it is approved
                             set TXT_EXISTS=1                                                      %+ rem If the lyric file exists, flag the situation as such
                             set coloring=%ansi_color_bright_green%                                %+ rem If the lyric file exists, draw debug info in green
                             set LYRIC_APPROVAL_VALUE=%@ExecStr[TYPE <"%txtfile%:lyrics" >&>nul]   %+ rem If the lyric file exists, get it’s approval status
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
set BAD=1 
                     endiff              
                     set NUM_PROCESSED=%@EVAL[%NUM_PROCESSED + 1]
                     iff 1 eq %BAD% then
                             title %EMOJI_WRENCH% Processed: %NUM_PROCESSED%
                             set remaining=%@EVAL[%remaining - 1]
                             set msg=%emoji_gear% Remaining:%italics_on%%@sans_serif[%remaining%]%italics_off% %emoji_gear%
                             call status-bar "%msg%"
                             rem   *pause>nul
                             set ANY_BAD=1
                             echo %EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%%unquoted_audio_file% 
                             echo repeat 13 echo. `%`+ call get-lyrics "%unquoted_audio_file%" >>:u8"%tmpfile_cfml_1%"
                             set NUM_BAD=%@EVAL[NUM_BAD + 1]
                             rem echo now %NUM_BAD% bad ones
                     endiff                        
                     rem DEBUG: echo %ansi_color_normal%* Checking %faint_on%%AudioFile%%faint_off% %@ansi_move_to_col[65] txtfile=%faint_on%%txtfile%%faint_off% %tab% %@ANSI_MOVE_TO_COL[125]%coloring%EXISTS=%txt_exists%%ansi_color_normal%   %coloring2%APPROVED=%LYRIC_APPROVAL_VALUE%
             return
        :process_file_end

rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


:END
:Cleanup
        rem While we’re here, do some cleanup: if exist *.json ((del /q *.json) >&nul)
endlocal        