@Echo OFF

if "%@FUNCTION[randfg]" == "" function RANDFG=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`

repeat %@EVAL[%_ROWS*%_COLUMNS] echos %@randfg[]%@if[%@RANDOM[0,1] gt 0,%faint_on%,]%@if[%@RANDOM[0,1]gt0,%blink_on%,]%@CHAR[9733]%blink_off%%faint_off% 

*pause >nul