@loadbtm on

@rem     Removes a tag associated with a file, using Windows Alternate Data Streams for files. 

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
:USAGE: remove-ADS-tag-from-file filename.txt  [tag_name]  [verbose]
:USAGE: 
:USAGE:         EXAMPLE: remove-ADS-tag-to-file filename.txt songlyrics.txt lyrics 
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ sets the “lyrics” tag to blank
:USAGE: VERBOSE MODE: ( 3ʳᵈ arg is "verbose"):
:USAGE:
:USAGE:         Verifies what happens on-screen.
endtext
%COLOR_NORMAL%
if not defined DefaultUnicodeOutput set DefaultUnicodeOutput=no
set //UnicodeOutput=%DefaultUnicodeOutput%
call divider
return


:init

rem Usage:
        if "%1" EQ "" (gosub :usage %+ goto :END)

rem Get parameters:
        set   FILE_TO_USE=%@UNQUOTE[%1]                                            %+ rem file to use 
        set TAG_TO_REMOVE=%@UNQUOTE[%2]                                            %+ rem ads tag to remove/blank out
        set               PARAM_3=%3                                               %+ rem "verbose" if you want on-screen verification of what’s happeneing

rem Validate environment (once):
        iff "1" != "%validated_rm_ads_tag_from_file%" then
                call validate-environment-variables ansi_colors_have_been_set
                set  validated_rm_ads_tag_from_file=1
        endiff

rem Validate parameters (every time):
        if not exist "%File_To_Use%" call validate-environment-variable  File_To_Use   "1ˢᵗ arg to %0 must be a filename. 2ⁿᵈ optional arg must be a tag, 3ʳᵈ arg can be “verbose”"
        if "" ==   "%tag_to_remove%" call validate-environment-variable  Tag_To_Remove "2ⁿᵈ argument %0 must be a tag to remove, NOT empty"

rem Set default values for parameters:
        set VERBOSE=0
        if "%TAG_TO_REMOVE%" == ""  (set TAG_TO_REMOVE=tag)


rem Remove tag: 
        call add-ADS-tag-to-file "%FILE_TO_USE%" %TAG_TO_REMOVE% remove %PARAM_3% %4$
:END

