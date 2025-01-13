@Echo OFF
@loadbtm on
@setdos /x0
rem @on break cancel
rem @setlocal


rem CONFIGURATION:
        set most_songs_from_playlist_to_process_at_a_time=100 %+ rem 🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐


:DESCRIPTION: Checks for files that are missing *approved* lyric files.
:USAGE: check-for-missing-lyrics {etc} ————————————————————— checks files in current folder, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics get {etc} ————————————————— checks files in current folder, and  gets all  the missing lyrics
:USAGE:
:USAGE: check-for-missing-lyrics playlist.m3u {etc} ———————— checks files in   playlist.m3u, and displays songs missing lyrics
:USAGE: check-for-missing-lyrics get playlist.m3u {etc} ———— checks files in   playlist.m3u, and  gets all  the missing lyrics
:USAGE: 
:USAGE: check-for-missing-lyrics karaoke playlist.m3u {etc} ———— checks files in   playlist.m3u, and  gets all  the missing karaoke
:USAGE: 
:USAGE:  ... where {etc} are options that will be passed directly to get-lyrics.bat, such as “genius” or ““force”



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
                        if not defined ANSI_CURSOR_VISIBLE      set ANSI_CURSOR_VISIBLE=%@CHAR[27][?25h
                        if not defined BLINK_ON                 set BLINK_ON=%@CHAR[27][6m
                        if not defined CURSOR_RESET             set CUROR_RESET=%@CHAR[27][ q%@CHAR[27]]12;#CF5500%@CHAR[7]%@CHAR[27][1 q
                        set validated_cfml_ansi=1
                endiff

rem Validate environment once per session:
        iff 1 ne %VALIDATED_CFMLB% then
                call validate-is-function ANSI_MOVE_UP ANSI_CURSOR_COLOR_BY_WORD                   %+ rem would be more portable to bring these definitions into this file
                call validate-in-path set-tmpfile get-lyrics.bat get-karaoke.bat perl randomize-file.pl errorlevel pause-for-x-seconds divider beep.bat set-tmp-file.bat status-bar.bat
                set  VALIDATED_CFMLB=1                                                             
        endiff                




rem If we were supplied a filename, process it as a list of files:                                 %+ rem This script can run in a couple different modes, so we need to deal with that
        set PARENT=%@UNQUOTE[%@NAME["%_PBATCHNAME"]]
        set GET=0                                                                                  %+ rem Our default mode is GET=0, which means we will not be running the generated script afterward
        set ETC=0                                                                                  %+ rem Extra options to be passed directly to get-lyrics.bat, such as “genius” or “force”
        rem echo processing... %%0=“%0”, %%* is “%*”, %%1 is “%1”, %%2 is “%2”, %%1$ is “%1$” %+ pause
        iff "%1" != "" then                                                                        %+ rem If an argument was given, it should be "get", a filename, or a filename followed by "get"
                iff "%1" == "get" .or. "%1" == "karaoke" then                                      %+ rem if "get" was passed, we are actually going to run the script that this script generates. Adjust the flag for that               
                        if "%1" != "get"     set GET=0
                        if "%1" == "get"     set GET=1
                        if "%1" != "karaoke" set GET_KARAOKE=0
                        if "%1" == "karaoke" set GET_KARAOKE=1
                        set FILELIST_MODE=0
                        set Filelist_to_Check_for_Missing_Lyrics_in=
                        shift

                        rem This code block is bad form that should not exist:
                        iff "%@EXT[%@UNQUOTE["%1"]]" == "m3u" then
                                rem echo it’s an m3u! limit=%limit%
                                set most_songs_from_playlist_to_process_at_a_time=1000
                                set FILELIST_MODE=1
                                set Filelist_to_Check_for_Missing_Lyrics_in=%@UNQUOTE["%1"]
                                call validate-environment-variable Filelist_to_Check_for_Missing_Lyrics_in %+ rem       ...and make sure the filename is a file that actually exists
                                rem moved below call important "Finding songs with missing %findNature% in playlist: %italics_on%“%emphasis%%@NAME[%Filelist_to_Check_for_Missing_Lyrics_in%].%@EXT[%Filelist_to_Check_for_Missing_Lyrics_in%]%italics_off%%deemphasis%”%conceal_on%1111%conceal_off%"
                                shift
                        endiff

                else                                                                               %+ rem if "get" was passed  *WITH* a filename...
                        set  FILELIST_MODE=1                                                       %+ rem       ...set our operational mode flag appropriately...
                        set  Filelist_to_Check_for_Missing_Lyrics_in=%@UNQUOTE["%1"]               %+ rem       ...store the filename parameter for later...
                        shift
                        call validate-environment-variable Filelist_to_Check_for_Missing_Lyrics_in %+ rem       ...and make sure the filename is a file that actually exists
                        rem repeat 7 echo.
                        rem call divider
                        rem moved below call important "Finding %blink_on%%limit%%blink_off% songs with missing %italics_on%%findNature%%italics_off% in playlist: %italics_on%“%emphasize%%@NAME[%Filelist_to_Check_for_Missing_Lyrics_in%].%@EXT[%Filelist_to_Check_for_Missing_Lyrics_in%]%deemphasis%%italics_off%”%conceal_on%2222%conceal_off%"
                        iff "%1" == "get" then                                                    
                                set GET=1                                                         
                                shift                                                             
                        endiff
                endiff                
                set ETC=%1$
        else                                                                                       %+ rem If run without parameters...
                set  Filelist_to_Check_for_Missing_Lyrics_in=                                      %+ rem       ...we are not using a fileist, so make sure that variable is empty
                set  FILELIST_MODE=0                                                               %+ rem       ...we are not using a fileist, so make sure the proper operational flag is set
        endiff                       
        rem DEBUG: echo Filelist_to_Check_for_Missing_Lyrics_in=%Filelist_to_Check_for_Missing_Lyrics_in% filelist_mode=%filelist_mode% %+ pause   %+ rem Debug
        rem DEBUG:





rem Set our getter, depending on whether we’re in lyric mode, or “hidden” karaoke mode:
        iff 1 ne %GET_KARAOKE then
                set GETTER=get-lyrics
                set findNature=lyrics
        else
                set GETTER=create-srt
                set findNature=karaoke
        endiff

        rem DEBUG: 



rem Debug:
        rem echo ETC is “%ETC%”, GET=“%GET%”, GET_KARAOKE=“%GET_KARAOKE%”, GETTER=“%GETTER%”, NATURE=“%findNature”, flielist_mode=“%flielist_mode%”, limit=“%limit%” %%*=“%*”, %%1=“%1” %+ pause



rem Go through each audio file, seeing if it lacks approved lyrics:
        set ANY_BAD=0                                                                              %+ rem Track if we found *any* bad files at all
        set NUM_BAD=0
        set NUM_PROCESSED=0
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        set tmpfile2=%tmpfile%
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        set tmpfile_cfml_1=%tmpfile%
        
        rem DEBUG: echo tmpfile  is %tmpfile_cfml_1%%newline%tmpfile2 is %tmpfile2% %+ pause

        iff 0 eq %FILELIST_MODE% then 
                set ENTITY_TO_USE=%FILEMASK_AUDIO%
                set LIMIT=9999
                if "%@FILES[%filemask_audio%]" !=  "" set LIMIT=%@FILES[%filemask_audio%]
        else    
                set LIMIT=%most_songs_from_playlist_to_process_at_a_time%
                randomize-file.pl  <"%Filelist_to_Check_for_Missing_Lyrics_in%" >%tmpfile2%
                set ENTITY_TO_USE=@"%tmpfile2%"
        endiff
        



rem Remaining parameter processing: For if we pass a number to set a manual limit:
        set next=%1
        shift
        iff "%next%" ne "" then
                setdos /x-5
                        iff "1" == "%@RegEx[^[0-9]+$,%@UNQUOTE["%next%"]]" then
                                set LIMIT=%next%
                                shift
                        else
                                rem Nope...
                        endiff
                        setdos /x0
        endiff



rem Let user know what’s going on:
        repeat 5 echo.
        iff 1 eq %FILELIST_MODE then
                set in= in playlist: %italics_on%“%emphasis%%@NAME[%Filelist_to_Check_for_Missing_Lyrics_in%].%@EXT[%Filelist_to_Check_for_Missing_Lyrics_in%]%deemphasis%%italics_off%”
        else
                set in= in %@NAME[%_CWD]
        endiff
        gosub divider
        echo.
        call important "Finding %blink_on%%limit%%blink_off% songs with missing %italics_on%%findNature%%italics_off%%IN%"
        echo.



rem Debug:        
        rem echo ETC is “%ETC%”, GET=“%GET%”, GET_KARAOKE=“%GET_KARAOKE%”, GETTER=“%GETTER%”, NATURE=“%findNature”, flielist_mode=“%flielist_mode%”, limit=“%limit%” %%*=“%*”, %%1=“%1” %+ pause






rem If we are processing a playlist OR a wildcard set of files, look through it for audio files, 
rem and add lines generating the missing lyrics (if any found) to %tmpfile_cfml_1:
        set remaining=%limit%
        set limit_reached=0
        setdos /x-4
        for %%CFML_AudioFile in (%ENTITY_TO_USE%) do (
                gosub process_file "%CFML_AudioFile%" 
                rem echo NUM_BAD=%NUM_BAD%
                if %NUM_BAD ge %LIMIT (
                        set limit_reached=1
                        leavefor 
                )
        )    
        setdos /x0
        rem not always! (2025/01/04) call status-bar unlock
        echos %ansi_save_position%
        for %%offset in (-1) do (
               echos %@ansi_move[%@EVAL[%_rows-%offset],0]%ansi_erase_to_eol%
        )                
        echos %ansi_restore_position%
        
        
rem If we have reached our limit, stop processing        
        if %ANY_BAD gt 0 repeat 4 echo.
        iff 1 eq %limit_reached then
                repeat 1 call beep.bat highest
                call bigecho "%ansi_color_warning_soft%%check%   Limit of: %italics_on%%blink_on%%@formatn[3.0,%LIMIT%]%blink_off%%italics_off% files %ansi_color_success%reached%ansi_color_normal%"
        else                
                repeat 1 call beep.bat highest
        endiff

        
rem Display post-processing statistics:
        iff %num_processed eq 0 then
                echo.
                echo.
                call warning "No files were processed here!" silent
                echo %ansi_reset% >nul
                echo.
                echo.
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
                echo ━━━━━━━━━━━━━━━━━━ Current dir is %_CWD ━━━━━━━━━━━━ >nul
                call bigecho %ANSI_COLOR_BRIGHT_GREEN%%CHECK%  Processed: %italics_on%%@FORMATn[3.0,%NUM_PROCESSED%]%italics_off% songs 
                call bigecho %ANSI_COLOR_BRIGHT_GREEN%%CHECK%    Located: %ansi_color_red%%@FORMATn[3.0,%NUM_BAD%]%ansi_color_bright_green% songs needing %findNature% attention
                call bigecho %ANSI_COLOR_BRIGHT_GREEN%%CHECK% Compliance: %@ANSI_RGB[%our_r%,%our_g%,%our_b%]%@formatn[3.1,%clean_formatted_percent%]%cool_percent%
                echo.
        endiff


rem Create the fix-script, if there are any to fix:
        setdos /x0
        iff 1 eq %ANY_BAD% then                                                                           %+ rem We generate a script to find the missing ones, but if and only if some missing ("bad") ones were found
                set TARGET_SCRIPT=get-the-missing-lyrics-here-temp.bat                                    %+ rem don’t change this!! Not w/o changing in clean-up-AI-transcription-trash-files and possibly in other places ... In some cases this may actually be getting the missing karaoke here and be a bit of a misnomer, sorry!
                if "%findNature%" eq "karaoke" set TARGET_SCRIPT=get-the-missing-karaoke-here-temp.bat    %+ rem don’t change this!! Not w/o changing in clean-up-AI-transcription-trash-files and possibly in other places ... In some cases this may actually be getting the missing karaoke here and be a bit of a misnomer, sorry!
                echo @Echo OFF                                          >:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: initialize: turn Echo OFF
                echo @setdos /x-4                                      >>:u8 "%TARGET_SCRIPT"
                rem Rexx says try x-3 here but i’m not so sure
                rem echo @on break cancel                              >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: initialize: make ^C/^Break work better
                echo.                                                  >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                type %tmpfile_cfml_1% |:u8 randomize-file.pl           >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: randomize the order of our script to eliminate alphabetical bias
                echo.                                                  >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                echo.                                                  >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                rem echo goto :skip_subs                               >>:u8 "%TARGET_SCRIPT"           
                rem echo         :process [file]                       >>:u8 "%TARGET_SCRIPT"
                rem echo                 repeat 8  echo.               >>:u8 "%TARGET_SCRIPT"
                rem echo                 setdos /x-4                   >>:u8 "%TARGET_SCRIPT"
                rem echo                 echo call get-lyrics %%file%% >>:u8 "%TARGET_SCRIPT"
                rem echo                 setdos /x0                    >>:u8 "%TARGET_SCRIPT"
                rem echo                 call  divider                 >>:u8 "%TARGET_SCRIPT"
                rem echo         return                                >>:u8 "%TARGET_SCRIPT"
                rem echo :skip_subs                                    >>:u8 "%TARGET_SCRIPT"
                echo @setdos /x0                                       >>:u8 "%TARGET_SCRIPT"
                echo :END                                              >>:u8 "%TARGET_SCRIPT"
                
rem Run the fix-script, if we have decided to:
                iff 1 eq %GET .or. 1 eq %GET_KARAOKE then                                          %+ rem If we have decided to auto-run the script, the let’s do that
                        rem title "Fetching lyrics!"
                        echos %@CHAR[27][%[_rows]H %+ rem Move to bottom of screen
                        repeat 3 echo.
                        gosub divider
                        echo.
                        gosub divider
                        echo.
                        echos %@ANSI_MOVE_UP[3]%ANSI_CURSOR_VISIBLE%
                        echos %@ANSI_CURSOR_COLOR_BY_WORD[yellow]                                  %+ rem Impotent because cursor color is set in pause-for-x-seconds anyway!
                        echos %ansi_color_green%Going to find those missing %findNature% now!%ansi_color_bright_Red%%blink_on%
                        sleep 1
                        echos %CURSOR_RESET%
                        echos %blink_off%
                        rem echo type "%TARGET_SCRIPT%" %+ type "%TARGET_SCRIPT%"                  %+ rem Debug
                                 call "%TARGET_SCRIPT%"                                            %+ rem run the generated script !X--X!
                        call   errorlevel                                                          %+ rem check for errorlevel //rem DEBUG: echo our_errorlevel is %our_errorlevel% 
                        if "" != "%original_title%" (*title %original_title%)                
                        rem echo pbatchmame_check-for-missing-lyrics_bat=%_PBATCHNAME >
                endiff
        endiff
        
        
        
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
        
        goto :process_file_end                                                                     %+ rem Skip over subroutines
             :process_file [CFML_AudioFile]
                        rem “Processing file: ”
                                rem @echo %ANSI_COLOR_DEBUG%- DEBUG: Processing file: “%CFML_AudioFile%” %ANSI_COLOR_NORMAL% 🐞 

                        rem Get our filenames (pretty messed up what you have to do to get a file like “whatever .mp3” with a space before the extension to work!):
                                setdos /x-4
                                set unquoted_audio_file=%@UNQUOTE[%CFML_AudioFile%]``
                                if "%@LEFT[4,%unquoted_audio_file%]" == "\\?\" set unquoted_audio_file=%@RIGHT[%@len[%unquoted_audio_file%-4],%unquoted_audio_file%]  %+ rem Fix filename if it begins with "\\?\" which is a network thingamabob:                                
                                set unquoted_audio_file_full=%@unquote[%@full[%CFML_audiofile%]``]``                                                                    %+ rem do NOT use full on unquoted_audio_file!
                                set audio_file_name=%@unquote[%@name[%unquoted_audio_file_full%``]``]``
                                set audio_file_path=%@unquote[%@path[%unquoted_audio_file_full%``]``]``

                        rem Return if the file doesn’t exist:
                                iff not exist "%unquoted_audio_file%" then
                                        echo %ansi_color_alarm%%blink_on%%EMOJI_WARNING% file doesn’t exist: “%unquoted_audio_file%”%ansi_color_normal%%blink_off%
                                        setdos /x0
                                        return
                                endiff
                        
                        rem Debug stuff:
                                goto :nope_1
                                        echo 🐞 %ansi_color_purple%CFML_AudioFile          =%CFML_AudioFile%%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%unquoted_audio_file     =“%unquoted_audio_file%”%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%unquoted_audio_file_full=“%unquoted_audio_file_full%”%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%audio_file_name         =“%audio_file_name%”%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%audio_file_path         =“%audio_file_path%”%ansi_color_normal% 🐞 
                                :nope_1

                        rem Reject if it’s an m3u-specific comment-line in the filelist:
                                if "%@LEFT[8,%unquoted_audio_file%]" == "#EXTINF:" return

                        rem Reject if the file doesn’t exist at all:                                
                                iff not exist %CFML_AudioFile% then
                                     echo %ansi_color_yellow% %EMOJI_CROSS_MARK% songfile doesn’t exist:        %faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                endiff

                        rem If the song is marked for approved-lyriclessness, the file is good:                                
                                set LYRICLESSNESS_APPROVAL_VALUE=%@ExecStr[TYPE "%unquoted_audio_file_full%:lyriclessness" >&>nul]         %+ rem get the song’s lyriclessness approval status
                                iff "APPROVED" == "%LYRICLESSNESS_APPROVAL_VALUE%" then
                                        set BAD=0
                                        goto :done_processing_this_file
                                endiff                                        

                        rem Special instrumental handling?
                                rem iff 1 eq %@RegEx[\(instrumental\),%@UNQUOTE[%CFML_AudioFile%]] then
                                rem endiff                     
                                
                        rem Determine filenames for lyric/karaoke files (which may or may not exist):                                
                                set txtfile=%audio_file_path%%audio_file_name%.txt                            %+ rem Create the filename of the lyric file that we will be looking for
                                set srtfile=%audio_file_path%%audio_file_name%.srt                            %+ rem Create the filename of the  srt  file that may exist
                                set lrcfile=%audio_file_path%%audio_file_name%.lrc                            %+ rem Create the filename of the  lrc  file that may exist


                        rem Debug stuff:
                                goto :nope_2
                                        echo 🐞 %ansi_color_purple%CFML_audiofile=%CFML_audiofile%%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%audio_file_path=%audio_file_path%%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%srtfile        =%srtfile% %ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%lrcfile        =%lrcfile% %ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%audio_file     =%audio_file%%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%txtfile        =%txtfile% %ansi_color_normal% 🐞 
                                :nope_2
                                
                        rem Song is considered "bad" [does not have approved lyrics], until we find the accompanying files and mark it as "good"
                                set BAD=1                                                                     


                        rem Check if the potential karaoke files exist, and if they do, the file is good:
                                if exist "%SRTfile%" .or. exist "%LRCfile%" (
                                        set BAD=0
                                ) else (
                                        set BAD=1
                                )

                                     
                        rem Check if the lyrics files already exists, and if so, then check if it is pre-approved:
                        rem (Unless we are in karaoke mode, then we don’t care about the lyric files)
                                iff 1 ne %GET_KARAOKE then
                                        iff exist "%[txtfile]" then                                                                                         %+ rem If the lyric file exists, we must check if it is approved
                                                set rem=DEBUG: call debug "Textfile %txtfile% already exists"
                                                set TXT_EXISTS=1                                                                                            %+ rem If the lyric file exists, flag the situation as such
                                                set coloring=%ansi_color_bright_green%                                                                      %+ rem If the lyric file exists, draw debug info in green
                                                set         LYRIC_APPROVAL_VALUE=%@ExecStr[TYPE  <"%txtfile%:lyrics"  >&>nul]                               %+ rem If the lyric file exists, get it’s approval status
                                                iff "APPROVED" == "%LYRIC_APPROVAL_VALUE%" .or. "APPROVED" == "%LYRICLESSNESS_APPROVAL_VALUE%" then         %+ rem If the lyrics are approved...
                                                        set coloring2=%coloring%                                                                            %+ rem    ...use the same success color for the text file
                                                        set BAD=0                                                                                           %+ rem Mark it as "good" [having approved lyrics] by un-setting "bad"
                                                else                                                                                                        %+ rem If the lyrics are NOT approved...
                                                        set LYRIC_APPROVAL_VALUE=%bright_red%Nope%ansi_color_normal%                                        %+ rem    ...set a meaningful display value like "Nope"
                                                        set coloring2=%ansi_color_bright_red%                                                               %+ rem    ...set the color to an alarming "angry" color
                                                endiff                                                                                                      
                                        else                                                                                                                %+ rem If the lyrics don’t exist at all,
                                                set rem=DEBUG: call debug "Textfile “%txtfile%” DOES NOT EXIST"                                                        
                                                set TXT_EXISTS=0                                                                                            %+ rem    ...set a flag storing this fact
                                                set coloring=%ansi_color_bright_black%                                                                      
                                                set coloring2=%ansi_color_bright_black%                                                                     
                                                set LYRIC_APPROVAL_VALUE=%NO%                                                                               %+ rem    ...set a meaningful display value like "🚫"
                                                set BAD=1 
                                        endiff            
                                endiff
                        rem Debug:
                                rem DEBUG: echo   bad is %BAD% for %txtfile% ... txt_exists=%txt_exists% 🐐
                        
                        rem Keep track of how many files we’ve processed in total:
                                :done_processing_this_file
                                set NUM_PROCESSED=%@EVAL[%NUM_PROCESSED + 1]
                                
                        rem Display the # processed (which only applies to bad files):
                                title To find: %remaining% ... Tried: %NUM_PROCESSED%
                                
                        rem If this file is bad, deal with that:
                                iff 1 eq %BAD% then
                                                                               
                                        rem Display the # remaining as a status bar at the bottom of the screen:
                                                setdos /x0
                                                set remaining=%@EVAL[%remaining - 1]
                                                set msg=%emoji_gear% Remaining:%italics_on%%@sans_serif[%remaining%]%italics_off% %emoji_gear%
                                                if 1 ne %DONT_MESS_WITH_MY_STATUS_BAR% call status-bar "%msg%"
                                                rem   *pause>nul
                                        
                                        rem Keep track of if/how many bad files there were:
                                                set ANY_BAD=1
                                                set NUM_BAD=%@EVAL[NUM_BAD + 1]
                                                rem echo now %NUM_BAD% bad ones

                                        rem Warn of missing lyrics:                                        
                                                echos %@ANSI_MOVE_TO_COL[1]%EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%
                                                      setdos /x-4
                                                      echo %unquoted_audio_file%
                                                      setdos /x0
                                                
                                        rem Add lyric-retrieval command to our autorun script:
                                              rem echo gosub process "%unquoted_audio_file%" >>:u8"%tmpfile_cfml_1%"
                                              setdos /x-4

                                              iff 1 eq %GENIUS_ONLY% then
                                                      echo repeat 7 echo. `%`+ if exist "%unquoted_audio_file%" .and. not exist "%@unquote[%@name["%unquoted_audio_file%"]].txt" call %GETTER% "%unquoted_audio_file%" %ETC% `%`+ call  divider >>:u8"%tmpfile_cfml_1%"
                                              else
                                                      echo repeat 7 echo. `%`+ if exist "%unquoted_audio_file%"                                                                  call %GETTER% "%unquoted_audio_file%" %ETC% `%`+ call  divider >>:u8"%tmpfile_cfml_1%"
                                              endiff
                                              rem we added the and not exist part right here --------------------^^^^^^^^ for genius mode, TODO consider whether that should also be there during normal mode or not. After we do our full-collection genius-only download, this should emergently become more apparant
                                              setdos /x0
                                                    
                                endiff                        
                                rem DEBUG: echo %ansi_color_normal%* Checking %faint_on%%CFML_AudioFile%%faint_off% %@ansi_move_to_col[65] txtfile=%faint_on%%txtfile%%faint_off% %tab% %@ANSI_MOVE_TO_COL[125]%coloring%EXISTS=%txt_exists%%ansi_color_normal%   %coloring2%APPROVED=%LYRIC_APPROVAL_VALUE%
             setdos /x0
             
             rem call debug "Done with loop!"
             
             return
        :process_file_end

rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


:END
:Cleanup
        rem While we’re here, do some cleanup: if exist *.json ((del /q *.json) >&nul)
        rem endlocal        


        goto :skip_subs_cfml
                :divider []
                        rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                        set wd=%@EVAL[%_columns - 1]
                        set nm=%bat%\dividers\rainbow-%wd%.txt
                        iff exist %nm% then
                                *type %nm%
                                if "%1" != "NoNewline" .and. "%2" != "NoNewline" .and. "%3" != "NoNewline" .and. "%4" != "NoNewline" .and. "%5" != "NoNewline"  .and. "%6" != "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                        else
                                echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                        endiff
                return
        :skip_subs_cfml
