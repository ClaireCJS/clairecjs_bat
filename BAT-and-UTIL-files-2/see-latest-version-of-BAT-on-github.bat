@Echo OFF
@on break cancel

iff exist "c:\bat\%@UNQUOTE[%1]" .or. exist "c:\notes\%@UNQUOTE[%1]" then
        echo https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/%@UNQUOTE[%1]
else 
        call warning "%@UNQUOTE[%1].bat doesn't exist!"
        https://github.com/ClaireCJS/clairecjs_bat/
endiff