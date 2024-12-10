@Echo OFF

set    LRC_file=%@UNQUOTE[%1]
set output_file=%@NAME[%lrc_file].txt

call validate-environment-variable   LRC_file 
call validate-is-extension         "%LRC_file%"  *.lrc

if exist "%Output_file%" call deprecate "%output_file%" >&>nul
lrc2txt.py %*

call validate-environment-variable output_file
call review-files "%LRC_FILE%" "%output_file%"



