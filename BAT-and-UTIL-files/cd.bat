@Echo Off

rem Keep track of the last folder we're in —— this is done automatically in other ways but we want our own
        set LAST_FOLDER=%_CWD

rem If there are fewer files than when we entered the folder, let us know:
        set LAST_FOLDER_EXITED_NUMFILES=%@FILES[.,-d]
        if     %LAST_FOLDER_ENTERED_NUMFILES ne %LAST_FOLDER_ENTERED_NUMFILES (
            if %LAST_FOLDER_ENTERED_NUMFILES lt %LAST_FOLDER_ENTERED_NUMFILES (set VERB=reduced)
            if %LAST_FOLDER_ENTERED_NUMFILES gt %LAST_FOLDER_ENTERED_NUMFILES (set VERB=increased)
            call less_important "%italics_on%%VERB%%italics_off% number of files from %bold_on%%LAST_FOLDER_ENTERED_NUMFILES%%bold_off% to %bold_on%%LAST_FOLDER_EXITED_NUMFILES%%bold_off%"
        )


rem Change into the folder —— the actual thing we mean to do 😂 —— and count the files
        *cd   %*
        set LAST_FOLDER_ENTERED_NUMFILES=%@FILES[.,-d]

rem Change the window title to the folder, while keeping track of the last couple titles:
        if "%*" ne "" (
            if defined LAST_TITLE (set LAST_TITLE_2=%LAST_TITLE%)
            set        LAST_TITLE=%_wintitle
            title %*
        )

rem Keep track of the number of files in the folder:
        set NUM_FILES=%@FILES[.,-d]

rem Stuff we don't normally do is coming up —— so color it a warning color to some extent
        %COLOR_WARNING%

rem Rename extensions we don't ever want to exist:
            if exist *.jpg_large (ren /E *.jpg_large *.jpg >&nul)
            if exist *.jpg!d     (ren /E *.jpg!d     *.jpg >&nul)

rem Delete files we don't ever want to exist:
            if exist  thumbs.db  (                     *del /z  thumbs.db ) %+ rem ::::: cruft: Windows 
            if exist desktop.ini (                     *del /z desktop.ini) %+ rem ::::: cruft: Windows 
            if exist       a.out (                     *del /z       a.out) %+ rem ::::: cruft: Unix
            if exist       *.pkf (                     *del /z       *.pkf) %+ rem ::::: cruft: CoolEdit/Audition 
            if exist       *.mta (sweep if exist *.mta *del /z       *.mta) %+ rem ::::: cruft: Samsung Allshare 
            if exist   clear     (call warning "'clear' file found!%newline%" %+ call divider %+ type clear %+ call divider %+ *del /p clear) %+ rem ::::: cruft: wget calls to WinAmp's wawi plugin


%COLOR_NORMAL%
