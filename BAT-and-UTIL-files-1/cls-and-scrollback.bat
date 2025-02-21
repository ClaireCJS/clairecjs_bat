@Echo OFF

if not defined %ANSI_CLS_AND_SCROLLBACK call validate-environment-variable ANSI_CLS_AND_SCROLLBACK
*cls
cls
echos %ANSI_CLS_AND_SCROLLBACK%
