@LoadBTM ON
@Echo OFF
@on break cancel


rem Check usage:
        iff "%1" == "" then
                echo.
                call warning "Please provide text to copy to clipboard, or a filename to load to the clipboard"
                goto :END
        endiff





rem 2025: Let’s comment out this fixclip.bat kludge: unset /q TMP


rem Check if the first argument is a filename or not:
                      set filename_for_clip=None
        if exist "%1" set filename_for_clip=%1
        if exist  %1  set filename_for_clip=%1


rem Copy text or filename to clipboard, depending on the nature of our input:
        iff "%filename_for_clip%" == "None" then
                @echo %* >:u8 clip:
        else 
                load_to_clipboard.py %*
        endiff





:END

