@Echo OFF
@loadbtm on
@setdos /x0
rem 20250328 let’s try removing this: @setlocal
cls
rem @on break cancel


rem CONFIGURATION:
        set most_songs_from_playlist_to_process_at_a_time=25 




:DESCRIPTION: Checks for files that are missing *approved* lyric files.
:USAGE:
:USAGE: check-for-missing-lyrics {etc} ————————————————————————— checks files in current folder, and displays a list of songs missing lyrics
:USAGE: check-for-missing-lyrics get {etc} ————————————————————— checks files in current folder, and retrieves/aligns all the missing lyrics
:USAGE:
:USAGE: check-for-missing-lyrics karaoke playlist.m3u {etc} ———— checks files in  playlist.m3u, and retrieves/generates all the missing karaoke/transcriptions
:USAGE:
:USAGE: check-for-missing-lyrics playlist.m3u {etc} ———————————— checks files in playlist.m3u, and displays a list of songs missing lyrics
:USAGE: check-for-missing-lyrics get playlist.m3u {etc} ———————— checks files in playlist.m3u, and retrieves/aligns all the missing lyrics:USAGE: 
:USAGE: 
:USAGE:  ... where {etc} are options that will be passed directly to get-lyrics.bat, such as “genius” or “force”, 
:USAGE:                  or a number that is the limit of the # of files to find in a playlist search (because that can take time!)
:USAGE:



rem Environment variable backups —— these should all already be defined already, but if not, define them here:
        echos %ANSI_COLOR_NORMAL%
        set original_title=%_TITLE
        rem Are our required filemasks set?
                iff "1" != "%FILEMASKS_HAVE_BEEN_SET%" then
                        if not defined FILEMASK_AUDIO           set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.ra;*.dtshd;*.m4a;*.aif
                        if not defined FILEMASK_VOCAL           set FILEMASK_VOCAL=*.mp3;*.wav;*.rm;*.voc;*.au;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.ra;*.dtshd;*.m4a;*.aif
                endiff
        rem Are our required emoji set?
                iff "1" != "%EMOJIS_HAVE_BEEN_SET%" then
                        if not defined DASH                     set DASH=%@REPEAT[%@CHAR[9135],2]
                        if not defined NO                       set NO=%@CHAR[55357]%@CHAR[57003]
                        if not defined EMOJI_CHECK_MARK         set EMOJI_CHECK_MARK=%@CHAR[10004]%@CHAR[65039]
                endiff                
        rem Are our required ansi values set?
                iff "1" != "%ANSI_COLORS_HAVE_BEEN_SET%" .and. "1" != "%validated_cfml_ansi%" then
                        if not defined            BRIGHT_RED    set            BRIGHT_RED=%@CHAR[27][91m
                        if not defined ANSI_COLOR_BRIGHT_RED    set ANSI_COLOR_BRIGHT_RED=%@CHAR[27][91m
                        if not defined ANSI_COLOR_BRIGHT_PURPLE set ANSI_COLOR_BRIGHT_PURPLE=%@CHAR[27][38;2;255;0;255m
                        if not defined ANSI_COLOR_MAGENTA       set ANSI_COLOR_MAGENTA=%@CHAR[27][38;2;170;0;85m
                        if not defined ANSI_CURSOR_VISIBLE      set ANSI_CURSOR_VISIBLE=%@CHAR[27][?25h
                        if not defined BLINK_ON                 set BLINK_ON=%@CHAR[27][6m
                        if not defined CURSOR_RESET             set CUROR_RESET=%@CHAR[27][ q%@CHAR[27]]12;#CF5500%@CHAR[7]%@CHAR[27][1 q
                        set validated_cfml_ansi=1
                endiff



rem HALT CONDITIONS:  (copy to check-for-missing-lyrics & check-for-missing-karaoke but change _fail_type varname & don’t fail getting lyrics for untranscribeable & change printed “Sorry!”):
        rem HALT ❶: If the folder indicates something we shouldn’t be creating karaoke for, let the user know:
        rem (copied from create-srt but with %_CWD\ substitued over %FULL_FILENAME%)
                rem Reset our failure flag(s):
                        unset /q cfml_fail_type cfml_fail_point *_in_foldname

                rem Check to see if certain halt patterns are in our folder names:
                        set instr_in_foldname=%@REGEX["[\[\(][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][sS]*[\)\]\\]","%_CWD\"]
                        set chipt_in_foldname=%@REGEX["[\\\[\(][cC][hH][iI][pP][tT][uU][nN][eE][sS]*[\\\]\)]","%_CWD%\"]
                        set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*[\\\]\)]","%_CWD\"]                                    %+ rem OLD
                        set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*","%_CWD\"]                                            %+ rem NEW: to commodate folder names like “sound effects & ambient sound”
                        set sndcl_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [cC][lL][iI][pP][sS]*","%_CWD\"]                                                    %+ rem NEW: to commodate folder names like  “sound clips & ambient sound”
                        set novoc_in_foldname=%@REGEX["[nN][oO] [vV][oO][cC][aA][lL][sS]*","%_CWD\"]                                                    
                        set nolyr_in_foldname=%@REGEX["[nN][oO] [lL][yY][rR][iI][cC][sS]*","%_CWD\"]                                                    
                        set untra_in_foldname=%@REGEX["[\\\[\(][Uu][Nn][Tt][Rr][Aa][Nn][Ss][Cc][Rr][Ii][Bb][Ee]*[Aa][Bb][Ll][Ee][\\\]\)]","%_CWD\"]

                rem If certain halt patterns ARE in our filename, gather our failure type:
                        if "1" == "%instr_in_foldname%" ( set cfml_fail_type=instrumental     %+ set cfml_fail_point=dir name)
                        if "1" == "%untra_in_foldname%" ( set cfml_fail_type=untranscribeable %+ set cfml_fail_point=dir name)
                        if "1" == "%chipt_in_foldname%" ( set cfml_fail_type=chiptune         %+ set cfml_fail_point=dir name)
                        if "1" == "%sndfx_in_foldname%" ( set cfml_fail_type=sound effects    %+ set cfml_fail_point=dir name)
                        if "1" == "%sndcl_in_foldname%" ( set cfml_fail_type=sound clips      %+ set cfml_fail_point=dir name)
                        if "1" == "%novoc_in_foldname%" ( set cfml_fail_type=no vocals        %+ set cfml_fail_point=dir name)
                        if "1" == "%nolyr_in_foldname%" ( set cfml_fail_type=no lyrics        %+ set cfml_fail_point=dir name)

                rem Signal our failure to any other processes watching this environment variable:
                        if "dir name" == "%cfml_fail_point%" set BAD_AI_TRANSCRIPTION_FOLDER=%_CWP                  

                rem DEBUG: 
                        if "1" == "%DEBUG_AUTOFAIL_FOLDERS%" pause "cmfk_fail_type=“%cfml_fail_type%” chipt_in_foldname=“%chipt_in_foldname%” sndfx_in_foldname=“%sndfx_in_foldname%”" 

                rem Let user know if we halted based on one of our halt conditions:
                        iff "" != "%cfml_fail_type%" then
                                echo %ansi_color_warning%%no% Sorry! Not checking for missing lyrics here because this %italics_on%%cfml_fail_point%%italics_off% indicates a %ansi_color_red%%italics_on%%blink_on%%cfml_fail_type%%blink_off%%italics_off%%ANSI_COLOR_WARNING% folder:%ansi_color_normal% %faint_on%“%_CWP%”%faint_off%%ansi_color_normal%
                                set  fail=1
                                call sleep 1
                                goto /i END
                        endiff




rem Validate environment once per session:
        iff "1" != "%VALIDATED_CFMLB%" then
                call validate-is-function ANSI_MOVE_UP ANSI_CURSOR_COLOR_BY_WORD                   %+ rem would be more portable to bring these definitions into this file
                call validate-in-path set-tmpfile get-lyrics.bat get-karaoke.bat perl randomize-file.pl errorlevel pause-for-x-seconds divider beep.bat set-tmp-file.bat status-bar.bat delete-bad-ai-transcriptions
                echos %@ANSI_MOVE_TO_COL[1]
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


                        iff "%@EXT[%@UNQUOTE["%1"]]" == "m3u" then
                                rem echo it’s an m3u! limit=%limit%
                                rem set most_songs_from_playlist_to_process_at_a_time=1000
                                if "%@Regex[![0-9]+!,!%2!]" == "1" set most_songs_from_playlist_to_process_at_a_time=%2
                                rem echo most_songs_from_playlist_to_process_at_a_time is %most_songs_from_playlist_to_process_at_a_time%
                                set FILELIST_MODE=1
                                set Filelist_to_Check_for_Missing_Lyrics_in=%@UNQUOTE["%1"]
                                if not exist "%Filelist_to_Check_for_Missing_Lyrics_in%" call validate-environment-variable Filelist_to_Check_for_Missing_Lyrics_in %+ rem       ...and make sure the filename is a file that actually exists
                                rem moved below call important "Finding songs with missing %findNature% in playlist: %italics_on%“%emphasis%%@NAME[%Filelist_to_Check_for_Missing_Lyrics_in%].%@EXT[%Filelist_to_Check_for_Missing_Lyrics_in%]%italics_off%%deemphasis%”%conceal_on%1111%conceal_off%"
                                shift
                        endiff

                else                                                                               %+ rem if "get" was passed  *WITH* a filename...
                        set  FILELIST_MODE=1                                                       %+ rem       ...set our operational mode flag appropriately...
                        set  Filelist_to_Check_for_Missing_Lyrics_in=%@UNQUOTE["%1"]               %+ rem       ...store the filename parameter for later...
                        shift
                        if not exist "%validate-environment-variable Filelist_to_Check_for_Missing_Lyrics_in%" call validate-environment-variable Filelist_to_Check_for_Missing_Lyrics_in %+ rem       ...and make sure the filename is a file that actually exists
                        rem repeat 7 echo.
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



rem Check for fast mode:
        iff "%1" == "fast" then
                set CFML_FAST=1
        else
                set CFML_FAST=0
        endiff



rem Kill bad transcriptions unless in fast mode:
        if "0" != "%DELETE_BAD_AI_TRANSCRIPTIONS_FIRST%" .and. "1" != "%CFML_FAST%" .and. exist *.srt call delete-bad-ai-transcriptions 3
        setdos /x0





rem Set our getter, depending on whether we’re in lyric mode, or “hidden” karaoke mode:
        iff "1" != "%GET_KARAOKE%" then
                set GETTER=get-lyrics-for-file.btm
                set findNature=lyrics
        else
                set GETTER=create-srt-from-file
                set findNature=karaoke
        endiff

        rem DEBUG: 



rem Debug:
        rem echo ETC is “%ETC%”, GET=“%GET%”, GET_KARAOKE=“%GET_KARAOKE%”, GETTER=“%GETTER%”, NATURE=“%findNature”, flielist_mode=“%flielist_mode%”, limit=“%limit%” %%*=“%*”, %%1=“%1” %+ pause, CFML_FAST=“%CFML_FAST%”



rem Go through each audio file, seeing if it lacks approved lyrics:
        set ANY_BAD=0                                                                              %+ rem Track if we found *any* bad files at all
        set NUM_BAD=0
        set NUM_PROCESSED=0
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        set tmpfile2=%tmpfile%
        call set-tmpfile                                                                           %+ rem Sets temporary file to %tmpFile
        set tmpfile_cfml_1=%tmpfile%
        
        rem DEBUG: echo tmpfile  is %tmpfile_cfml_1%%newline%tmpfile2 is %tmpfile2% %+ pause

        iff "0" == "%FILELIST_MODE%" then 
                set ENTITY_TO_USE=%FILEMASK_vocal%
                set LIMIT=9999
                if "%@FILES[%filemask_vocal%]" !=  "" set LIMIT=%@EVAL[%@FILES[%filemask_vocal%] * 2]  %+ rem doubling it out of pure superstition
        else    
                set LIMIT=%most_songs_from_playlist_to_process_at_a_time%
                randomize-file.pl  <"%Filelist_to_Check_for_Missing_Lyrics_in%" >%tmpfile2%
                set ENTITY_TO_USE=@"%tmpfile2%"
        endiff
        



rem Remaining parameter processing: For if we pass a number to set a manual limit:
        set next=%1
        shift
        iff "%next%" != "" then
                *setdos /x-5
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
        iff "1" eq "%FILELIST_MODE%" then
                set in= in playlist: %italics_on%“%emphasis%%@NAME[%Filelist_to_Check_for_Missing_Lyrics_in%].%@EXT[%Filelist_to_Check_for_Missing_Lyrics_in%]%deemphasis%%italics_off%”
                set limit_to_use=%limit%
        else
                set in= in: %italics_on%“%emphasis%%@NAME[%_CWD]%deemphasis”
                set limit_to_use=
        endiff
        gosub divider
        echo.

        rem call important "Finding %@IF["%limit_to_use%" != "",%blink_on%%limit%%blink_off% ,]songs with missing %italics_on%%findNature%%italics_off%%IN%"
        set  tmpmsg=Finding %@IF["%limit_to_use%" != "",%blink_on%%limit%%blink_off% ,]songs with missing %italics_on%%findNature%%italics_off%%IN%
        title %tmpmsg%
        call important "%tmpmsg%"
        echo.



rem Debug:        
        rem echo ETC is “%ETC%”, GET=“%GET%”, GET_KARAOKE=“%GET_KARAOKE%”, GETTER=“%GETTER%”, NATURE=“%findNature”, flielist_mode=“%flielist_mode%”, limit=“%limit%” %%*=“%*”, %%1=“%1” %+ pause



rem COSMETIC CONFIG:
        rem MISSING_FILE_PRE_TEXT is the part of :process_file that we moved out for slight speed optimization
        set MISSING_FILE_PRE_TEXT=%@ANSI_MOVE_TO_COL[1]%EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%

rem If we are processing a playlist OR a wildcard set of files, look through it for audio files, 
rem and add lines generating the missing lyrics (if any found) to %tmpfile_cfml_1:
        set remaining=%limit%
        set limit_reached=0
        *setdos /x-4
        for %%CFML_AudioFile in (%ENTITY_TO_USE%) do (
                gosub process_file "%CFML_AudioFile%" 
                rem echo NUM_BAD=%NUM_BAD%
                if %NUM_BAD ge %LIMIT (
                        set limit_reached=1
                        leavefor 
                )
        )    
        setdos /x0
        rem not always! (2025/01/04) 
        rem maybe always? (2025/03/03)
        call status-bar unlock
        echos %ansi_save_position%
        for %%offset in (-1) do (
               echos %@ansi_move[%@EVAL[%_rows-%offset],0]%ansi_erase_to_eol%
        )                
        echos %ansi_restore_position%
        
        
rem If we have reached our limit, stop processing        
        if %ANY_BAD gt 0 repeat 4 echo.
        iff "1" == "%limit_reached%" then
                repeat 1 call beep.bat highest
                call bigecho "%ansi_color_warning_soft%%check%   Limit of: %italics_on%%blink_on%%@formatn[3.0,%LIMIT%]%blink_off%%italics_off% files %ansi_color_success%reached%ansi_color_normal%"
        else                
                repeat 1 call beep.bat highest
        endiff

        
rem Display post-processing statistics:
        if "%num_processed%" != "0" goto :num_proc_ne_0
                echo.
                echo.
                call warning "No files were processed here!" silent
                echos %ansi_reset% >nul
                echo.
                echo.
                goto :done_with_displaying_postprocessing_statistics
        :num_proc_ne_0
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
                rem flags not accurate: if "" != "%ANY_BAD%" .and. "0" != "%ANY_BAD%" echo.
                rem To conditionalize this next echo we’d have to keep trakc of whether there’s any output at all, not just any_bad...:
                call status-bar unlock
                echo.
                echo ━━━━━━━━━━━━━━━━━━ Current dir is %_CWD ━━━━━━━━━━━━ >nul
                call bigecho "%ANSI_COLOR_BRIGHT_GREEN%%CHECK%  Processed: %italics_on%%@FORMATn[3.0,%NUM_PROCESSED%]%italics_off% songs"
                call bigecho "%ANSI_COLOR_BRIGHT_GREEN%%CHECK%    Located: %ansi_color_red%%@FORMATn[3.0,%NUM_BAD%]%ansi_color_bright_green% songs needing %findNature% attention"
                set compliance_string=%@formatn[3.1,%clean_formatted_percent%]%cool_percent%
                call bigecho "%ANSI_COLOR_BRIGHT_GREEN%%CHECK% Compliance: %@ANSI_RGB[%our_r%,%our_g%,%our_b%]%compliance_string%"
                title %CHECK%Compliance: %compliance_string%
                echo.
        :done_with_displaying_postprocessing_statistics

rem Create the fix-script, if there are any to fix:
        setdos /x0
        if "1" !=  "%ANY_BAD%" goto :no_bad_detected                                                      %+ rem We generate a script to find the missing ones, but if and only if some missing ("bad") ones were found
                set TARGET_SCRIPT=get-the-missing-lyrics-here-temp.bat                                    %+ rem don’t change this!! Not w/o changing in clean-up-AI-transcription-trash-files and possibly in other places ... In some cases this may actually be getting the missing karaoke here and be a bit of a misnomer, sorry!
                if "%findNature%" == "karaoke" set TARGET_SCRIPT=get-the-missing-karaoke-here-temp.bat    %+ rem don’t change this!! Not w/o changing in clean-up-AI-transcription-trash-files and possibly in other places ... In some cases this may actually be getting the missing karaoke here and be a bit of a misnomer, sorry!
                echo @Echo OFF                                          >:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: initialize: turn Echo OFF
                echo @*setdos /x-4                                      >>:u8 "%TARGET_SCRIPT"
                rem Rexx says try x-3 here but i’m not so sure
                rem echo @on break cancel                              >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: initialize: make ^C/^Break work better
                echo.                                                  >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                type %tmpfile_cfml_1% |:u8 randomize-file.pl           >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: randomize the order of our script to eliminate alphabetical bias
                echo.                                                  >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                echo.                                                  >>:u8 "%TARGET_SCRIPT"             %+ rem get-missing-lyrics script: cosmetics:  script starts with a blank line
                rem echo goto :skip_subs                               >>:u8 "%TARGET_SCRIPT"           
                rem echo         :process [file]                       >>:u8 "%TARGET_SCRIPT"
                rem echo                 repeat 8  echo.               >>:u8 "%TARGET_SCRIPT"
                rem echo                 *setdos /x-4                  >>:u8 "%TARGET_SCRIPT"
                rem echo                 echo call get-lyrics %%file%% >>:u8 "%TARGET_SCRIPT"
                rem echo                 setdos /x0                    >>:u8 "%TARGET_SCRIPT"
                rem echo                 call  divider                 >>:u8 "%TARGET_SCRIPT"
                rem echo         return                                >>:u8 "%TARGET_SCRIPT"
                rem echo :skip_subs                                    >>:u8 "%TARGET_SCRIPT"
                echo @setdos /x0                                       >>:u8 "%TARGET_SCRIPT"
                echo :END                                              >>:u8 "%TARGET_SCRIPT"
                
                rem Run the fix-script, if we have decided to:
                        setdos /x0
                        if "1" == "%GET%" .or. "1" == "%GET_KARAOKE%" goto :fetch_lyrics_begin
                                                                      goto :fetch_lyrics_end
                                :fetch_lyrics_begin
                                        rem title "Fetching lyrics!"
                                        echos %@CHAR[27][%[_rows]H %+ rem Move to bottom of screen
                                        repeat 3 echo.
                                        gosub divider
                                        echo.
                                        gosub divider
                                        echo.
                                        echos %@ANSI_MOVE_UP[3]%ANSI_CURSOR_VISIBLE%%@ANSI_CURSOR_COLOR_BY_WORD[yellow]
                                        call bigecho "%ansi_color_green%%STAR% Going to find those missing %findNature% now!%ansi_color_bright_red% %STAR%"
                                        gosub divider
                                        sleep 1
                                        set TARGET_SCRIPT_TO_CALL=%@NAME[%TARGET_SCRIPT%]-%[_datetime].bat
                                        echo %CURSOR_RESET%%blink_off%
                                        iff exist "%TARGET_SCRIPT%" then
                                                echos %ansi_color_unimportant%
                                                *ren /Ns "%TARGET_SCRIPT%" "%TARGET_SCRIPT_TO_CALL%"
                                        endiff
                                        :target_script_exists_1
                                                if not exist "%TARGET_SCRIPT_TO_CALL%" call warning "Why doesn’t TARGET_SCRIPT_TO_CALL exist? “%TARGET_SCRIPT_TO_CALL%”'
                                                if     exist "%TARGET_SCRIPT_TO_CALL%" call "%TARGET_SCRIPT_TO_CALL%"                                             %+ rem run the generated script !X--X!
                                                if     exist "%TARGET_SCRIPT_TO_CALL%" call errorlevel                                                            %+ rem check for errorlevel //rem DEBUG: echo our_errorlevel is %our_errorlevel% 
                                        :target_script_exists_2
                                        if "" != "%original_title%" (*title %original_title%)                
                                        rem echo pbatchname_check-for-missing-lyrics_bat=%_PBATCHNAME 
                                :fetch_lyrics_end
        :no_bad_detected
        
        
        
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


        
        goto :process_file_end                                                                     %+ rem Skip over subroutines
             :process_file [CFML_AudioFile]
                        rem “Processing file: ”
                                rem @echo %ANSI_COLOR_DEBUG%- DEBUG: Processing file: “%CFML_AudioFile%” %ANSI_COLOR_NORMAL% 🐞 

                        rem If no filename given, it’s an erroneous/extraneous call and we shouldn’t do anything:
                                iff "%UNQUOTE[%CFML_AUDIOFILE%]" == "" .or. %CFML_AUDIOFILE% == "" then
                                        echo [Returning due to null filename being passed]
                                        return
                                endiff
                        rem CMFL_Audiofile checks:
                                rem Reject if the file is one of our trash filenames:
                                        rem "1" == "%@RegEx[[\(\[]instrumental[\)\]],%@UNQUOTE[%CFML_AudioFile%]]" then rem Error 2025/07/25
                                        set namey=%@FULL[%@UNQUOTE[%CFML_AudioFile%]]
                                        if "" == "%namey%" set namey=NULL
                                        iff "1" == "%@RegEx[[\(\[]instrumental[\)\]],%namey%]" then
                                             echo %ansi_color_yellow%%@CHAR[10060]%@CHAR[0] songfile is instrumental: %zzzz%%faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                             return                                
                                        endiff
                                        iff "1" == "%@RegEx[[\(\[\\]chiptunes?[\)\]\\],%namey%]" then
                                             echo %ansi_color_yellow%%@CHAR[10060]%@CHAR[0] songfile is chiptune: %zzzzzzzz%%faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                             return                                
                                        endiff
                                        rem ✪✪✪ We still want lyrics for untranscribeable songs, so let’s NOT do this: ✪✪✪
                                        rem ✪✪✪ Actualy, we do NOT want lyrics for untranscribeable songs. If we had them, we’d at least be able to hand-transcribe. ✪✪✪
                                        iff "1" == "%@RegEx[[\(\[\\]untranscribeable?[\)\]\\],%namey%]" then
                                             echo %ansi_color_yellow%%@CHAR[10060]%@CHAR[0] songfile is untranscribeable: %zzzzzzzzz%%faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                             return                                
                                        endiff
                                        iff "1" == "%@RegEx[[\(\[\\]sound effect?[\)\]\\],%namey%]" then
                                             echo %ansi_color_yellow%%@CHAR[10060]%@CHAR[0] songfile is sound effect: %zzzz%%faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                             return                                
                                        endiff
                                rem Reject if the file doesn’t exist at all:                                
                                        iff not exist "%@UNQUOTE["%CFML_AudioFile%"]" then
                                             echo %ansi_color_yellow%%EMOJI_CROSS_MARK% songfile doesn’t exist: %zzzzzzzzzz%%faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                             return
                                        endiff
                                rem Reject if the file is one of our trash filenames:
                                        iff "1" == "%@RegEx[_vad_.*_chunks.*\.wav,"%CFML_AudioFile%"]" then
                                             echo %ansi_color_yellow%%@CHAR[10060]%@CHAR[0] songfile is AI temp-file:       %faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                             return                                
                                        endiff

                        rem Get our filenames (pretty messed up what you have to do to get a file like “whatever .mp3” with a space before the extension to work!):
                                *setdos /x-4
                                rem Unquoted_audio_file filename:
                                        set unquoted_audio_file=%@UNQUOTE[%CFML_AudioFile%]``

                        rem Unquoted_audio_file checks:
                                if "%@LEFT[4,%unquoted_audio_file%]" == "\\?\" set unquoted_audio_file=%@RIGHT[%@len[%unquoted_audio_file%-4],%unquoted_audio_file%]  %+ rem Fix filename if it begins with "\\?\" which is a network thingamabob:                                
                                rem Return if it’s an m3u #EXTINF line
                                rem Reject if it’s an m3u-specific comment-line in the filelist:
                                        rem if "1" == "%@Regex[#EXTINF,"%unquoted_audio_file%"]" .or. "1" == "%@Regex[#EXTM3U,"%unquoted_audio_file%"]" return
                                        if "%@LEFT[8,%unquoted_audio_file%]" == "#EXTINF:"   .or. "%@LEFT[7,%unquoted_audio_file%]" == "#EXTM3U"    return
                                rem Return if the file doesn’t exist:
                                        if exist "%unquoted_audio_file%" goto :It_Exists
                                                echo %ansi_color_alarm%%blink_off%%EMOJI_WARNING% file doesn’t exist: “%unquoted_audio_file%”%ansi_color_normal%%blink_off%
                                                setdos /x0
                                                return
                                        :It_Exists

                        rem Define rest of the filenames:
                                set unquoted_audio_file_full=%@unquote[%@full[%CFML_audiofile%]``]``                                                                    %+ rem do NOT use full on unquoted_audio_file!
                                set audio_file_name=%@unquote[%@name[%unquoted_audio_file_full%``]``]``
                                set audio_file_path=%@unquote[%@path[%unquoted_audio_file_full%``]``]``
                        
                        rem Debug stuff:
                                goto :nope_1
                                        echo 🐞 %ansi_color_purple%CFML_AudioFile          =%CFML_AudioFile%%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%unquoted_audio_file     =“%unquoted_audio_file%”%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%unquoted_audio_file_full=“%unquoted_audio_file_full%”%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%audio_file_name         =“%audio_file_name%”%ansi_color_normal% 🐞 
                                        echo 🐞 %ansi_color_purple%audio_file_path         =“%audio_file_path%”%ansi_color_normal% 🐞 
                                :nope_1
                                          
                        rem gosub DeleteEverywhere               *._vad_collected_chunks*.wav
                        rem gosub DeleteEverywhere               *._vad_collected_chunks*.srt
                        rem gosub DeleteEverywhere               *._vad_original*.srt
                        rem gosub DeleteEverywhere               *._vad_pyannote_*chunks*.wav
                        rem gosub DeleteEverywhere               *._vad_pyannote_v3.txt
                        rem gosub DeleteEverywhere  create-the-missing-karaokes-here-temp*.bat
                        rem gosub DeleteEverywhere       get-the-missing-lyrics-here-temp*.bat
                        rem gosub DeleteEverywhere      get-the-missing-karaoke-here-temp*.bat

                        rem Special instrumental handling?
                                rem iff 1 eq %@RegEx[\(instrumental\),%@UNQUOTE[%CFML_AudioFile%]] then
                                rem endiff                     

                        rem If the song is marked for approved-lyriclessness, the file is good **IF WE ARE CHECKING FOR MISSING LYRICS** but ✨✨✨NOT✨✨✨ if we are checking for missing karaoke:                                
                                set LYRICLESSNESS_APPROVAL_VALUE=%@ExecStr[TYPE "%unquoted_audio_file_full%:lyriclessness" >&>nul]         %+ rem get the song’s lyriclessness approval status
                                rem echo LYRICLESSNESS_APPROVAL_VALUE=“%LYRICLESSNESS_APPROVAL_VALUE%” for “%unquoted_audio_file_full%:lyriclessness”
                                iff "APPROVED" == "%LYRICLESSNESS_APPROVAL_VALUE%" .and. "1" != "%GET_KARAOKE%" then
                                        echo %ansi_color_yellow%%@CHAR[10060]%@CHAR[0] %italics_on%%ansi_color_debug%%faint_on%[check-for-missing-lyrics]%faint_off%%italics_off%%ansi_color_yellow% songfile is marked lyricless:  %faint_on%%@UNQUOTE[%CFML_AudioFile%]%faint_off%``                        
                                        set BAD=0
                                        goto /i :done_processing_this_file
                                endiff                                        
                                
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
                                iff exist "%SRTfile%" then
                                        rem echo * Not bad because SRTfile exists: %SRTfile
                                        set BAD=0
                                endiff
                                iff exist "%LRCfile%" then 
                                        rem echo * Not bad because LRCfile exists: %SRTfile
                                        set BAD=0
                                endiff

                                     
                        rem Check if the lyrics files already exists, and if so, then check if it is pre-approved:
                        rem (Unless we are in karaoke mode, then we don’t care about the lyric files)
                                iff "1" != "%GET_KARAOKE%" then
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
                                                set rem=DEBUG: call debug "Textfile “%txtfile%” DOES NOT EXIST" silent
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
              
                        rem Change cursor every once in awhile to alleviate hangxiety:
                                if %@EVAL[%NUM_PROCESSED% mod 10] == 0 echos %@randcursor[]

                        rem Display the # processed (which only applies to bad files):
                                title To find: %remaining% ... Tried: %NUM_PROCESSED%
                                
                        rem If this file is bad, deal with that:
                                iff "1" == "%BAD%" then
                                                                               
                                        rem Display the # remaining as a status bar at the bottom of the screen:
                                                setdos /x0
                                                set remaining=%@EVAL[%remaining - 1]
                                                set msg=%emoji_gear% Remaining:%italics_on%%@sans_serif[%remaining%]%italics_off% %emoji_gear%
                                                if "1" != "%DONT_MESS_WITH_MY_STATUS_BAR%" call status-bar "%msg%"
                                                if "0" == "%REMAINING%"                    call status-bar unlock
                                                rem   *pause>nul
                                        
                                        rem Keep track of if/how many bad files there were:
                                                set ANY_BAD=1
                                                set NUM_BAD=%@EVAL[NUM_BAD + 1]
                                                rem echo now %NUM_BAD% bad ones

                                        rem Warn of missing lyrics:                                        
                                            rem echos %@ANSI_MOVE_TO_COL[1]%EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%
                                            rem Moved out of function for speedo optimization: set MISSING_FILE_PRE_TEXT=%@ANSI_MOVE_TO_COL[1]%EMOJI_WARNING% %ansi_color_warning_soft%Missing approved lyrics: %EMOJI_WARNING% %ansi_color_bright_purple%%DASH% %ansi_color_magenta%
                                                      *setdos /x-4
                                                echo %MISSING_FILE_PRE_TEXT%%unquoted_audio_file%
                                                      setdos /x0
                                                
                                        rem Add lyric-retrieval command to our autorun script:
                                              rem echo gosub process "%unquoted_audio_file%" >>:u8"%tmpfile_cfml_1%"
                                              *setdos /x-4
                                              iff "1" == "%GENIUS_ONLY%" then
                                                      echo repeat 7 echo. `%`+ if exist "%unquoted_audio_file%" .and. not exist "%@unquote[%@name["%unquoted_audio_file%"]].txt" call %GETTER% "%unquoted_audio_file%" %ETC% `%`+ call  divider >>:u8"%tmpfile_cfml_1%"
                                              else
                                                      echo repeat 7 echo. `%`+ if exist "%unquoted_audio_file%"                                                                  call %GETTER% "%unquoted_audio_file%" %ETC% `%`+ call  divider >>:u8"%tmpfile_cfml_1%"
                                              endiff
                                              rem we added the and not exist part right here --------------------^^^^^^^^ for genius mode, TODO consider whether that should also be there during normal mode or not. After we do our full-collection genius-only download, this should emergently become more apparant
                                              setdos /x0
                                                    
                                endiff                        
                                rem DEBUG: echo %ansi_color_normal%* Checking[cc] %faint_on%%CFML_AudioFile%%faint_off% %@ansi_move_to_col[65] txtfile=%faint_on%%txtfile%%faint_off% %tab% %@ANSI_MOVE_TO_COL[125]%coloring%EXISTS=%txt_exists%%ansi_color_normal%   %coloring2%APPROVED=%LYRIC_APPROVAL_VALUE%
             setdos /x0
             
             rem call debug "Done with loop!" silent
             
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

rem 20250328 let’s try removing this: @endlocal most_songs_from_playlist_to_process_at_a_time validated_cfml_ansi validated_cfmlb ANY_BAD NUM_BAD NUM_PROCESSED limit limit_reached compliance_pct target_script
