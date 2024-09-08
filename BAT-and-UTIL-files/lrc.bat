@Echo OFF

:USAGE: set SKIP_TEXTFILE_PROMPTING=1   {this is the default but pre-prompting with a companion text file can be turned off}
:USAGE: set SKIP_SEPARATION=1           {this is the default but separating  vocal   tracks  out  first   can be turned off}

:USAGE: lrc.bat whatever.mp3
:USAGE: lrc.bat whatever.mp3 keep       {keep vocal files after separation}
:USAGE: lrc.bat last                    {quick retry again at the point of creating the lrc file —— separated vocal files must already exist}

:REQUIRES: environment variables COLORS_HAVE_BEEN_SET (means our color-related shortcut environment variables have been defined), QUOTE (quote mark)
:DEPENDENCIES: whisper-faster.bat delete-zero-byte-files.bat validate-in-path.bat debug.bat error.bat warning.bat errorlevel.bat print-message.bat validate-environment-variable.bat





REM todo download lyrics
REM todo check if one exists in repostiroy already


REM validate environment
    timer /5 on
    call validate-in-path whisper-faster.bat debug.bat
    call validate-environment-variables COLORS_HAVE_BEEN_SET QUOTE


REM branch on certain paramters
    if "%1" eq "last" (goto :actually_make_the_lrc)


REM values set from parameters
    set           SONGFILE=%@UNQUOTE[%1]
    set           SONGBASE=%@NAME[%SONGFILE]
    set LRC_FILE=%SONGBASE%.lrc
    set TXT_FILE=%SONGBASE%.txt
    set JSN_FILE=%SONGBASE%.json
    set VOC_FILE=%SONGBASE%.vocals.wav
    set LRCFILE2=%SONGBASE%.vocals.lrc

REM our main input and output files
    set INPUT_FILE=%SONGFILE%
    SET EXPECTED_OUTPUT_FILE=%LRC_FILE%

REM display debug info
    call debug "\n    SONGFILE='%BIG_TOP%%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%':\n    %BIG_BOT%SONGFILE='%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%':\n\t\t%FAINT_ON%SONGBASE='%ITALICS_ON%%SONGBASE%%ITALICS_OFF%'\n\t\tLRC_FILE='%ITALICS_ON%%LRC_FILE%%ITALICS_OFF%', \n\t\tTXT_FILE='%ITALICS_ON%%TXT_FILE%%ITALICS_OFF%'%FAINT_OFF%\n"
    gosub say_if_exists SONGFILE
    gosub say_if_exists LRC_FILE
    gosub say_if_exists LRCFILE2
    gosub say_if_exists TXT_FILE
    gosub say_if_exists VOC_FILE
    gosub say_if_exists JSN_FILE
    echo.



REM if our input file doesn't exist, we have problems haha
    if not exist %INPUT_FILE% (call error "input file '%italics%%INPUT_FILE%%italics_off%' does not exist")

REM if an LRC file already exists, we shoudln't generate it
    if exist %LRC_FILE% (call error "Sorry, but %bold%LRC%bold_off% file '%italics%%LRC_FILE%%italics_off%' %underline%already%underline_off% exists!" %+ cancel)


REM if a text file of the lyrics exists, we need to engineer our AI transcription prompt with it to get better results
    set CLI_OPS=
    set SKIP_TEXTFILE_PROMPTING=1 %+ rem this is not what i thought it was!
    if not exist %TXT_FILE% .or. %SKIP_TEXTFILE_PROMPTING eq 1 (goto :No_Text)

        setdos /x-1
            set CLI_OPS=--initial_prompt "Transcribe this audio, keeping in mind that I am providing you with an existing transcription, which may or may not have errors, as well as header and footer junk that is not in the audio you are transcribing. Lines th at say 'downloaded from' should definitely be ignored. So take this transcription lightly, but do consider it. The contents of the transcription will have each line separated by ' / '.   Here it is: ``

            @echo off
            DO line IN @%TXT_FILE (
                set CLI_OPS=%CLI_OPS / %@REPLACE[%QUOTE%,',%line]
                REM echo %faint%Line is: %italics%%line%%italics_off%%faint_off%
            )

            set CLI_OPS=%CLI_OPS%"
        setdos /x0

    :No_Text






REM demucs vocals out
    REM decide if we do it or not
        if %SKIP_SEPARATION eq 1 (goto :Vocal_Separation_Skipped)
        if exist %VOC_FILE% (
            call warning "Vocal file '%italics%%VOC_FILE%%italics_off%' %underline%already%underline_off% exists! Using it..."
            goto :Vocal_Separation_Done
        )

    REM do it
        :Vocal_Separation
        call unimportant "Checking to see if demuexe.exe music-vocal separator is in the path ... For me, this is in anaconda3\scripts as part of Python"
        call validate-in-path demucs.exe

        REM mdx_extra model is way slower but in tneory slightly more accurate
        REM to use default, just set model= -- lack of parameter will use default
        REM Demucs 3 (Model B) may be best (9.92) which apparently mdx_extra is model b whereas mdx_extra_q is model b quantized faster but less accurate. but it's fast enough already!
            set MODEL_OPT=
            set MODEL_OPT=-n mdx_extra 


        REM actually demux the vocals out here
            %color_run%
            @Echo ON
            demucs.exe --filename "%_CWD\%VOC_FILE%" %MODEL_OPT% --verbose --device cuda --float32 --clip-mode rescale   "%SONGFILE%"
            @Echo OFF
            CALL errorlevel "Something went wrong with demucs.exe"


    REM validate if the vocal file was created, and remove demucs cruft           
        call validate-environment-variable VOC_FILE "demucs separation did not produce the expected file of '%VOC_FILE%'"

        :Vocal_Separation_Done
            set INPUT_FILE=%VOC_FILE%
            SET EXPECTED_OUTPUT_FILE=%LRCFILE2%
            if "%2" ne "keep" .and. isdir separated (rd /s /q separated)
        :Vocal_Separation_Skipped




REM does our input file exist?
        call validate-environment-variable  INPUT_FILE

REM actually create the LRC file
        :actually_make_the_lrc
        call whisper-faster.bat %CLI_OPS% "%INPUT_FILE%"

REM delete zero-byte LRC files that can be created
        call delete-zero-byte-files *.lrc

REM did we create the LRC file?
        call validate-environment-variable EXPECTED_OUTPUT_FILE "expected output file of '%italics%%EXPECTED_OUTPUT_FILE%%italics_off%' does not exist"



REM rename the file & delete the vocal-split wav file
    if "%EXPECTED_OUTPUT_FILE%" ne "%LRC_FILE%" (
        set MOVE_DECORATOR=%ANSI_GREEN%%FAINT%%ITALICS% 
        mv "%EXPECTED_OUTPUT_FILE%" "%LRC_FILE%"
    )
    call validate-environment-variable LRC_FILE "LRC file not found around line 123ish"
    if exist "%LRC_FILE%" .and. "%2" ne "keep" (*del /q /r "%VOC_FILE%")



goto :END

    :say_if_exists [it]
        if not defined %[it] (call error "say_if_exists called but it of '%it%' is not defined")
        set filename=%[%[it]]
        if exist %filename (
            set BOOL_DOES=1 %+ set does_punctuation=: %+ set does=%BOLD%%UNDERLINE%%italics%does%italics_off%%UNDERLINE_OFF%%BOLD_OFF%    ``
        ) else (
            set BOOL_DOES=0 %+ set does_punctuation=: %+ set does=does %FAINT%%ITALICS%%blink%not%blink_off%%ITALICS_OFF%%FAINT_OFF%
        )
        %COLOR_IMPORTANT_LESS%
            if %BOOL_DOES eq 0 (set DECORATOR_ON=  %strikethrough% %+ set DECORATOR_OFF=%strikethrough_off%)
            if %BOOL_DOES eq 1 (set DECORATOR_ON=%PARTY_POPPER%    %+ set DECORATOR_OFF=%PARTY_POPPER%     )
            echos * %it% %does% exist%does_punctuation% %FAINT%%decorator_on%%filename%%decorator_off%%FAINT_OFF%
        %COLOR_NORMAL%
        echo.
    return

:END

    timer /5 off
