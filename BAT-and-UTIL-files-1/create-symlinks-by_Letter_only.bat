@Echo OFF
 on break cancel

call validate-environment-variable ALL_MEDIA_BY_DRIVE 
rd   %ALL_MEDIA_BY_DRIVE%\*  >&>nul
for %letter in (%THE_ALPHABET%) if isdir %ALL_MEDIA_BY_DRIVE%\%letter% (echo * ERROR! %ALL_MEDIA_BY_DRIVE%\%letter% still exists! WTF! %+ pause %+ pause %+ pause %+ pause %+ pause %+ goto :END)
call create-symlinks byLetterOnly
