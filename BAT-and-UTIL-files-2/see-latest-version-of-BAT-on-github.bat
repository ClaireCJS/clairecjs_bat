@Echo OFF

iff exist "c:\bat\%@UNQUOTE[%1]" then
        https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/%@UNQUOTE[%1]
else 
        call warning "%@UNQUOTE[%1].bat doesn't exist!"
        https://github.com/ClaireCJS/clairecjs_bat/
endiff