@loadbtm on
@Echo Off
@on break cancel

rem CONFIG:
        iff not defined MY_MUSIC_COLLECTION_LOCATION .or. not isdir "%@UNQUOTE["%MY_MUSIC_COLLECTION_LOCATION%"]" then
                if not defined mp3                   .or. not isdir "%@UNQUOTE["%mp3%"]" call fatal_error "uh oh! my_music_collection_location does not exist, and the fallback variable of mp3 isn’t defined either"
                set MY_MUSIC_COLLECTION_LOCATION=%MP3% 
        endiff


rem Environment Validation happens way later in the file...



rem Forget previous values so we can re-check them:
        unset /q ALIGN_MUSIC_COLLECTION_LYRICS_MODE ANSWER ALIGN_MUSIC_COLLECTION_BEHAVIOR

rem Get timeout behavior if given:
                                         set PROMPT_MODE_GIVEN=0
        if "%1" == "0" .or. "%1" == "1" (set PROMPT_MODE_GIVEN=1 %+ set ALIGN_MUSIC_COLLECTION_LYRICS_MODE=%1 %+ shift)

rem Get behavior override parameters which should be 1st:
                                              set ALIGN_MUSIC_COLLECTION_BEHAVIOR=LyricAlignment
        if "%1" == "PromptAnalysis" (shift %+ set ALIGN_MUSIC_COLLECTION_BEHAVIOR=PromptAnalysis)

rem Get timeout type: (0=liad back, 1=thorough):
        rem Check if environment variables cause us to use thorough mode automatically:
                iff defined lyric_karaoke_alignment_thorough_mode .and.  "0" == "%PROMPT_MODE_GIVEN%" .and. ("0" == "%lyric_karaoke_alignment_thorough_mode%" .or. "1" == "%lyric_karaoke_alignment_thorough_mode%") then
                        set ALIGN_MUSIC_COLLECTION_LYRICS_MODE=%lyric_karaoke_alignment_thorough_mode%
                endiff

        rem Check if command line argument cause us to use thorough mode:
                iff "%1" == "0" .or. "%1" == "1" then
                        SET ALIGN_MUSIC_COLLECTION_LYRICS_MODE=%PARAM1%

        rem IF neither environment variable nor command-line argument tells us which mode, actually ask/prompt to user:
                else
                        rem First ask:
                                call bigecho "%star% Choose mode! %*"                                                                                                                
                                call AskYN "%ansi_color_bright_green%0%ansi_color_prompt%=laid-back-mode with timeout prompts, %ansi_color_bright_green%1%ansi_color_prompt%=thorough mode (no prompt timeouts)" 0 0 01 0:laid_back_mode,1:thorough_mode

                        rem Then check that the answer makes sense:
                                iff "%answer%" == "0" .or. "%answer%" == "1" then
                                        set ALIGN_MUSIC_COLLECTION_LYRICS_MODE=%ANSWER%
                                        set lyric_karaoke_alignment_thorough_mode=%ANSWER%
                        rem Otherwise completely fail as we’ve exhausted all possibilities here:
                                else
                                        call fatal_error "what kind of answer is “%ANSWER%”"
                                endiff
                endiff








rem Environment validation:
        if not isdir "%MY_MUSIC_COLLECTION_LOCATION%" call validate-environment-variable MY_MUSIC_COLLECTION_LOCATION
        iff "1" != "%validated__align_music_collection_lyrics_etc%" then
                call validate-environment-variables star ansi_color_bright_green ansi_color_prompt
                call validate-in-path get-lyrics get-karaoke sweep-random cd-for-sweep-random fatal_error askyn bigecho
                set  validated__align_music_collection_lyrics_etc=1
        endiff
                     








rem Go to root of your music collection:
        %MY_MUSIC_COLLECTION_LOCATION%\

rem Determine command to randomly sweep through collection with:
        if "%ALIGN_MUSIC_COLLECTION_BEHAVIOR%" == "LyricAlignment" set ALIGN_MUSIC_COLLECTION_BEHAVIOR=call get-lyrics here
        if "%ALIGN_MUSIC_COLLECTION_BEHAVIOR%" == "PromptAnalysis" set ALIGN_MUSIC_COLLECTION_BEHAVIOR=call get-karaoke here PromptAnalysis

rem Sweep randomly through the collection, running our planned behavior:
        echo %ansi_color_debug%%STAR% About to sweep-random with the command: “%ALIGN_MUSIC_COLLECTION_BEHAVIOR%”
        call sweep-random "%ALIGN_MUSIC_COLLECTION_BEHAVIOR%" force








rem Cleanup:
        :END
        unset /q ALIGN_MUSIC_COLLECTION_BEHAVIOR


