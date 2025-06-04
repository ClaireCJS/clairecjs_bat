@loadbtm on

@rem     Displays a tag associated with a file, using Windows Alternate Data Streams for files. 

@rem     These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn’t change things.



@Echo OFF
 on break cancel
 
goto :init

:usage
echo.
call divider
%COLOR_ADVICE%
set //UnicodeOutput=yes
text
:USAGE: display-ADS-tag-from-file filename.txt  [tag_name]  [verbose]
:USAGE: 
:USAGE:         EXAMPLE: remove-ADS-tag-to-file filename.txt songlyrics.txt lyrics 
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ displays the "lyrics” tag 
:USAGE: VERBOSE MODE: ( 2ⁿᵈ arg is "verbose"):
:USAGE:
:USAGE:         Displays it HARDER 😂
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
        set    FILE_TO_USE=%@UNQUOTE[%1]                                           %+ rem file to use 
        set TAG_TO_DISPLAY=%@UNQUOTE[%2]                                           %+ rem ads tag to display
        set                  PARAM_3=%3                                            %+ rem "verbose" if you want MORE on-screen verification of what’s happeneing

rem Validate environment (once):
        iff 1 ne %validated_disp_ads_tag_from_file% then
                call validate-environment-variables ansi_colors_have_been_set
                set  validated_disp_ads_tag_from_file=1
        endiff

rem Validate parameters (every time):
        call validate-environment-variable File_To_Use    "1ˢᵗ arg must be a filename. 2ⁿᵈ optional arg must be a tag, 3ʳᵈ arg can be “verbose”"
        call validate-environment-variable Tag_To_Display "2ⁿᵈ argument must be a tag to remove, NOT empty"

rem Set default values for parameters:
        set VERBOSE=0
        if "%TAG_TO_DISPLAY%" eq ""  (set TAG_TO_DISPLAY=tag)


rem Remove tag: 
        iff "%PARAM_3%" ne "verbose" then
                call add-ADS-tag-to-file %FILE_TO_USE% %TAG_TO_DISPLAY% read
                iff "%RECEIVED_VALUE%" ne "" then
                        echo %RECEIVED_VALUE%
                else
                        echo %emphasis%%italics_on%(null)%italics_off%%deemphasis%
                endiff
        else
                call add-ADS-tag-to-file %FILE_TO_USE% %TAG_TO_DISPLAY% read verbose
        endiff
:END

