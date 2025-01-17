@echo off
set ENV_LINE=%@EXECSTR[*setdos |:u8 *findstr ESCAPE=]
*setdos /x-8
set fetched_escape_character=%@UNQUOTE[%@ReReplace[ESCAPE=,,"%env_line%"]]
echo %@CHAR[9733] Current escape character is %fetched_escape_character%
*setdos /x0
