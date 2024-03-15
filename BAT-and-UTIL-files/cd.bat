@Echo Off

::::: Change into the fucking folder:
    :echo *cd   %*
	*cd   %*


::::: Change the fucking window title:
	if "%*" ne "" title %*

%COLOR_WARNING%

::::: Fuck you, Samsung Allshare:
	if exist *.mta     (sweep if exist *.mta del *.mta)

::::: Fuck you, thumbs.db & desktop.ini:
	if exist  thumbs.db  *del /z  thumbs.db  
	if exist desktop.ini *del /z desktop.ini

::::: Fuck you, cooledit:
	if exist *.pkf *del *.pkf 

::::: Fuck you in particular:
	if exist a.out *del a.out

::::: Fuck you dumb extension:
	if exist *.jpg_large ren /E *.jpg_large *.jpg >&nul
	if exist *.jpg!d     ren /E *.jpg!d     *.jpg >&nul


::::: Kinda complicated thing with wget + wawi + winamp....
::::: I was leaving these messes for a long, long time.
::::: Whatever made them was modified to clean up after itself.
::::: But the messes remain, lurking here and there, visible once every blue moon:
	if exist clear     (echo. %+ echo *** "clear" file found: %+ echo. %+ type clear %+ echo. %+ *del /p clear)

%COLOR_NORMAL%
