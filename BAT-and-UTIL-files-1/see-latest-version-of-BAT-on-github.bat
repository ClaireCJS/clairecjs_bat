@Echo OFF
@on break cancel


rem Validate environment once:
        iff "1" != "%seelatverofbatongit%" then
                call validate-environment-variable ANSI_HAS_BEEN_SET
                call validate-in-path              AskYN  clip
                set  validated-seelatverofbatongit=1
        endiff

rem Check if the filename we are talking about is in \bat\ or \notes\:
        unset /q EARL
        iff exist "c:\bat\%@UNQUOTE[%1]" .or. exist "c:\notes\%@UNQUOTE[%1]" then
                set EARL=https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/%@UNQUOTE[%1]
        else 
                call warning "%@UNQUOTE[%1].bat doesn't exist!"
                set EARL=https://github.com/ClaireCJS/clairecjs_bat/        
        endiff

rem Go to whatever URL we decidedo n:
        iff "" != "%EARL%" then
                echo Copied to clipboard: %faint_on%%EARL%%faint_off%
                echo %EARL% >:u8clip:
                call AskYN "go there" yes 0
                if "Y" == "%ANSWER%" %EARL%
        endiff
