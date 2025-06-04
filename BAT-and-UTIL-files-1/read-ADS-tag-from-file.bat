@loadbtm on

@rem     Reads a tag associated with a file into %RECEIVED_VALUE%, using Windows Alternate Data Streams for files. 

@rem     These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn’t change things.


@rem    basically a copy of display-ads-tags-from-bat with different defaults 

@Echo OFF
 on break cancel
 
goto :init

:usage
echo.
gosub divider
%COLOR_ADVICE%
set //UnicodeOutput=yes
echo.
echo :USAGE: %ansi_color_bright_yellow%read-ADS-tag-from-file%ansi_color_yellow% [filename] [tag_name] [“verbose” `|` “lyrics” `|` “lyriclessness”]%ansi_color_advice%
echo :USAGE: 
echo :USAGE:         EXAMPLE: remove-ADS-tag-to-file filename.txt songlyrics.txt tagname 
echo :USAGE:                  `^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^` Sets %%RECEIVED_VALUE%% to the file’s “tagname” tag’s value
echo. 
echo :USAGE: VERBOSE MODE: ( 3ʳᵈ arg is "verbose"):
echo :USAGE:
echo :USAGE:         Displays it afterward
echo.
echo :USAGE: LYRICS MODE: ( 3ʳᵈ arg is "lyrics"):
echo :USAGE:
echo :USAGE:         Mode catered to lyric files
echo. 
echo.
%COLOR_NORMAL%
gosub divider
if not defined DefaultUnicodeOutput set DefaultUnicodeOutput=no
set //UnicodeOutput=%DefaultUnicodeOutput%
return


:init

rem Usage:
        if "%1" EQ "" (gosub :usage %+ goto :END)

rem Get parameters:
        set FILE_TO_USE=%@UNQUOTE["%1"]                                         %+ rem file to use 
        set TAG_TO_READ=%@UNQUOTE["%2"]                                         %+ rem ads tag to display
        set                PARAM_3=%3                                           %+ rem "verbose" if you want MORE on-screen verification of what’s happeneing
        set               PARAMS_3=%3$                                          %+ rem rest of the command tail

rem Validate environment (once):
        iff "1" != "%validated_read_ads_tag_from_file%" then
                call validate-environment-variables ansi_colors_have_been_set emoji_have_been_set
                set  validated_read_ads_tag_from_file=1
        endiff

rem Validate parameters (every time):
        iff "%4" ne "skip_validations" then
                if "" == "%File_To_Use%" call validate-environment-variable File_To_Use "1ˢᵗ argument must be a filename. 2ⁿᵈ optional arg must be a tag, 3ʳᵈ arg arg can be “verbose”"
                if "" == "%Tag_To_Read%" call validate-environment-variable Tag_To_Read "2ⁿᵈ argument must be a tag to read, NOT empty"
        endiff
        
rem Set default values for parameters:
        set VERBOSE=0
        if "%TAG_TO_READ%" eq ""  (set TAG_TO_READ=tag)


rem Read tag: 
        call add-ADS-tag-to-file "%FILE_TO_USE%" "%TAG_TO_READ%" read %PARAMS_3%
        rem iff "%PARAM_3%" ne "verbose" then
        rem         echo call add-ADS-tag-to-file "%FILE_TO_USE%" %TAG_TO_READ% read %PARAM_3%
        rem else
        rem         echo call add-ADS-tag-to-file "%FILE_TO_USE%" %TAG_TO_READ% read verbose
        rem endiff
:END

goto :skip_subroutines
        :divider []
                rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                set wd=%@EVAL[%_columns - 1]
                set nm=%bat%\dividers\rainbow-%wd%.txt
                iff exist %nm% then
                        *type %nm%
                        if "%1" ne "NoNewline" .and. "%2" ne "NoNewline" .and. "%3" ne "NoNewline" .and. "%4" ne "NoNewline" .and. "%5" ne "NoNewline"  .and. "%6" ne "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                else
                        echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                endiff
        return
:skip_subroutines
