@Echo OFF

iff "%1" eq "" then
        text
                :USAGE: lrc2txt whatever.lrc [silent] —— generates whatever.txt, if "silent" is 2nd option, then does so without post-review
        endtext
        goto :END
endiff

set    LRC_file=%@UNQUOTE[%1]
set output_file=%@NAME[%lrc_file].txt

call validate-environment-variable   LRC_file 
call validate-is-extension         "%LRC_file%"  *.lrc

if exist "%Output_file%" (call deprecate "%output_file%" >&>nul)

if "%2" ne "silent" call divider
lrc2txt.py "%LRC_file%"

call validate-environment-variable output_file
if "%2" ne "silent" call review-files "%LRC_FILE%" "%output_file%"

:END
