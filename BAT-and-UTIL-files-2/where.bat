@Echo off
 on break cancel


:DESCRIPTION: searches (greps) file set in %LOCATIONS% ... This is basically our textual database of where we put objects in our house so we don't lose them!







rem This script is a mess! It's just a glorified "grep %* %locations%" with various bells and whistles. But it works.























rem Cosmetics:
         if "%DEBUG"=="1" (echo on)
         echo.

rem Validate parameters & env:
        if "%1" eq "" (call error "Must provide something (regex allowed) to search for." %+ goto :END)


rem Fix the clipboard because when it is broken this is an annoying situation:
        call fixclip

rem Set up backup locations, including dropbox:
        set TARGET=%LOCATIONS%
        set ALTERNATETARGET=c:\recycled\locations.dat
        set DROPBOXTARGET=%DROPBOX%\locations.htm

rem Decide whether we are fetching a local versoin or not
        if     exist %TARGET (
            set CREATECACHE=1
            goto :nofetch
        )
        if not exist %TARGET (set TARGET=%ALTERNATETARGET)
        if     exist %TARGET (goto :nofetch)
        set TARGET=%DROPBOXTARGET%
        if     exist %TARGET (goto :nofetch)

                goto :nofetch
                    rem old code no longer used...
                    rem :: :fetch
                    rem :: echo Fetching from web...
                    rem :: call wget --user=claire --password=death http://claire.sheer.us/private/personal.htm
                    rem :: if not exist personal.htm (echo *** COULD NOT FETCH! %+ goto :END)
                    rem :: if     exist personal.htm move personal.htm %ALTERNATETARGET
                    rem :: set %CONTACTS=%ALTERNATETARGET
                :nofetch
                :targetFound

rem Actually search for our contacts:
        if "%DEBUG"=="1" echo command is: echo @grep -i --color=always   %1 %2 %3 %4 %5 %6 %7 %8 %9 "%TARGET%"
                                               @grep -i --color=always   %1 %2 %3 %4 %5 %6 %7 %8 %9 "%TARGET%"



rem Copy file to local cache so if it not available next time [i.e. machine turned off] we at least have an old copy:
      if "%MACHINENAME"=="HADES" (unset /q CREATECACHE)
      if "%CREATECACHE"=="1" .and. "%TARGET%" ne "%ALTERNATETARGET%" (echo yar|copy %TARGET %ALTERNATETARGET% >nul)



rem Cleanup
        :cleanup
            unset /q NEXT
            unset /q CREATECACHE
            :unset /q TARGET
            :unset /q ALTERNATETARGET

:END