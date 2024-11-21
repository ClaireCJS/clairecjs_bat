@Echo off
 on break cancel

iff     "%username%" eq "claire"  then
        call cursor-Claire.bat
elseiff "%username%" eq "carolyn" then
        call cursor-Carolyn.bat
else
        rem Don't do anything...   
endiff
