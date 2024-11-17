@Echo OFF

:DESCRIPTION: This makes——and changes into——a folder that is named YYYYMMDD after the current calendar date.

call now
call mcd %YYYYMMDD%
