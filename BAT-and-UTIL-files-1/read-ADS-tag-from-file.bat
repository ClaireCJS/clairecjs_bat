
@rem     Reads a tag associated with a file into %RECEIVED_VALUE%, using Windows Alternate Data Streams for files. 

@rem     These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn’t change things.


@rem    basically a copy of display-ads-tags-from-bat with different defaults 

@Echo OFF
 on break cancel
 
goto :init

:usage
echo.
call divider
%COLOR_ADVICE%
set //UnicodeOutput=yes
text
:USAGE: read-ADS-tag-from-file [filename] [tag_name]  [verbose]
:USAGE: 
:USAGE:         EXAMPLE: remove-ADS-tag-to-file filename.txt songlyrics.txt lyrics 
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Sets %%RECEIVED_VALUE%% to the file’s “lyric” tag’s value

:USAGE: VERBOSE MODE: ( 2ⁿᵈ arg is "verbose"):
:USAGE:
:USAGE:         Displays it afterward
endtext
%COLOR_NORMAL%
call divider
if not defined DefaultUnicodeOutput set DefaultUnicodeOutput=no
set //UnicodeOutput=%DefaultUnicodeOutput%
return


:init

rem Usage:
        if "%1" EQ "" (gosub :usage %+ goto :END)

rem Get parameters:
        set FILE_TO_USE=%@UNQUOTE[%1]                                           %+ rem file to use 
        set TAG_TO_READ=%@UNQUOTE[%2]                                           %+ rem ads tag to display
        set               PARAM_3=%3                                            %+ rem "verbose" if you want MORE on-screen verification of what’s happeneing
        set              PARAMS_3=%3$                                           %+ rem rest of the command tail

rem Validate environment (once):
        iff 1 ne %validated_read_ads_tag_from_file% then
                call validate-environment-variables emphasis deemphasis italics_on italics_off ansi_color_green normal_arrow bold_on bold_off faint_on faint_off
                set  validated_read_ads_tag_from_file=1
        endiff

rem Validate parameters (every time):
        call validate-environment-variable File_To_Use "1ˢᵗ arg must be a filename. 2ⁿᵈ optional arg must be a tag, 3ʳᵈ arg arg can be “verbose”"
        call validate-environment-variable Tag_To_Read "2ⁿᵈ argument must be a tag to read, NOT empty"

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

