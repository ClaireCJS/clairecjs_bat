@Echo OFF

::::: DETERMINE IF WE'VE BEEN HERE BEFORE:
    if exist cover.jpg mv cover.jpg cover.jpg~
    if exist cover.gif mv cover.gif cover.gif~ 
    if exist cover.png mv cover.png cover.png~


::::: DETERMINE IF WE SHOULDN'T BE HERE AT ALL:
    if defined SPECIAL_FOLDER_NAMES goto :SpecialFolderNames_Defined_YES
        set SPECIAL_FOLDER_NAMES=%BAT%\proprietary-mp3-folder-names.txt
        call validate-environment-variable SPECIAL_FOLDER_NAMES
    :SpecialFolderNames_Defined_YES    
    set THIS="%@UPPER[%@FILENAME[%_CWP]]"
    if "%1" eq "force" goto :force1
    for /f "tokens=1-9999" %d in (%SPECIAL_FOLDER_NAMES%) if %THIS% eq "%@UPPER[%d]" (gosub NotTheRightKindOfFolder "%d" %+ goto :END)
    :: ^^^ TODO: ^^ DO THIS IN MP3S AFTER WE'VE RE-DONE THE MANUAL EMBEDDING IN HIGHER QUALITY. it works. it's tested.
            goto :ThisIsIndeedTheRightKindOfFolder
                :NotTheRightKindOfFolder
                    %COLOR_WARNING% %+ echos *** Not the right kinda folder: "%1" %+ %COLOR_NORMAL% %+ echo.
                return
            :ThisIsIndeedTheRightKindOfFolder
            :force1

::::: FIND FIRST MP3:
    set AN_MP3=%@EXECSTR[ffind /f /m *.mp3]
    set AN_FLA=%@EXECSTR[ffind /f /m *.flac]
    %COLOR_DEBUG% %+ echo *** found  MP3?: %AN_MP3% %+ %COLOR_NORMAL%
    %COLOR_DEBUG% %+ echo *** found FLAC?: %AN_FLA% %+ %COLOR_NORMAL%


::::: EXTRACT ARTWORK:
    :NO: ffmpeg -i "%AN_MP3%" cover.jpg
    if "%AN_MP3" ne "" (metamp3-v0.91.exe   --save-pict       cover.jpg "%AN_MP3%" >nul)
    if "%AN_FLA" ne "" (metaflac          --export-picture-to cover.jpg "%AN_FLA%" >nul)
    if exist cover.jpg goto :Artwork_Created_Successfully

        :: complain if extraction failed:
            call warning "I guess things failed, because I don't see a cover.jpg"
            if exist cover.jpg~ (ren cover.jpg~ cover.jpg)
            %COLOR_NORMAL%  %+ beep %+ pause
            goto :END

        :: brag if  we succeed:
            :Artwork_Created_Successfully
            call success "Artwork successfully created: "
            %COLOR_LOGGING% %+ echos  "%_CWD\cover.jpg"
            %COLOR_NORMAL%  %+ echo. %+ echo.
            goto :END


:END

::::: CLEANUP BACKUPS THAT ARE THE SAME AS WHAT THEY ARE BACKING UP, AND ALSO (last 3 lines) DON'T HAVE FOLDER.JPG THAT DUPLICATES COVER.JPG:
     if exist  cover.jpg .and. exist  cover.jpg~ (%color_run% %+ echos %ITALICS_ON% %+ comp  cover.jpg  cover.jpg~ %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0 (%color_debug% %+ echo  cover.jpg~ is the same as cover.jpg,  so deleting.                %+ %color_removal% %+        *del  cover.jpg~          ))
     if exist  cover.gif .and. exist  cover.gif~ (%color_run% %+ echos %ITALICS_ON% %+ comp  cover.gif  cover.gif~ %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0 (%color_debug% %+ echo  cover.gif~ is the same as cover.gif,  so deleting.                %+ %color_removal% %+        *del  cover.gif~          ))
     if exist  cover.png .and. exist  cover.png~ (%color_run% %+ echos %ITALICS_ON% %+ comp  cover.png  cover.png~ %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0 (%color_debug% %+ echo  cover.png~ is the same as cover.png,  so deleting.                %+ %color_removal% %+        *del  cover.png~          ))
     if exist folder.jpg .and. exist folder.jpg~ (%color_run% %+ echos %ITALICS_ON% %+ comp folder.jpg folder.jpg~ %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0 (%color_debug% %+ echo folder.jpg~ is the same as folder.jpg, so deleting.                %+ %color_removal% %+        *del folder.jpg~          ))
     if exist folder.gif .and. exist folder.gif~ (%color_run% %+ echos %ITALICS_ON% %+ comp folder.gif folder.gif~ %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0 (%color_debug% %+ echo folder.gif~ is the same as folder.gif, so deleting.                %+ %color_removal% %+        *del folder.gif~          ))
     if exist folder.png .and. exist folder.png~ (%color_run% %+ echos %ITALICS_ON% %+ comp folder.png folder.png~ %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0 (%color_debug% %+ echo folder.png~ is the same as folder.png, so deleting.                %+ %color_removal% %+        *del folder.png~          ))
     if exist  cover.jpg .and. exist  cover.jpg~ (if %@FILESIZE[cover.jpg~]  gt %@FILESIZE[cover.jpg]                (%color_debug% %+ echo Oops, extracted art is smaller than pre-existing art. Backrolling! %+ %color_removal% %+ echo yr|mv  cover.jpg~  cover.jpg))
     if exist  cover.gif .and. exist  cover.gif~ (if %@FILESIZE[cover.gif~]  gt %@FILESIZE[cover.gif]                (%color_debug% %+ echo Oops, extracted art is smaller than pre-existing art. Backrolling! %+ %color_removal% %+ echo yr|mv  cover.gif~  cover.gif))
     if exist  cover.png .and. exist  cover.png~ (if %@FILESIZE[cover.png~]  gt %@FILESIZE[cover.png]                (%color_debug% %+ echo Oops, extracted art is smaller than pre-existing art. Backrolling! %+ %color_removal% %+ echo yr|mv  cover.png~  cover.png))
     if exist folder.jpg .and. exist folder.jpg~ (if %@FILESIZE[folder.jpg~] gt %@FILESIZE[folder.jpg]               (%color_debug% %+ echo Oops, extracted art is smaller than pre-existing art. Backrolling! %+ %color_removal% %+ echo yr|mv folder.jpg~ folder.jpg))
     if exist folder.gif .and. exist folder.gif~ (if %@FILESIZE[folder.gif~] gt %@FILESIZE[folder.gif]               (%color_debug% %+ echo Oops, extracted art is smaller than pre-existing art. Backrolling! %+ %color_removal% %+ echo yr|mv folder.gif~ folder.gif))
     if exist folder.png .and. exist folder.png~ (if %@FILESIZE[folder.png~] gt %@FILESIZE[folder.png]               (%color_debug% %+ echo Oops, extracted art is smaller than pre-existing art. Backrolling! %+ %color_removal% %+ echo yr|mv folder.png~ folder.png))
     if exist folder.jpg .and. exist cover.jpg   (%color_run% %+ echos %ITALICS_ON% %+ comp folder.jpg cover.jpg  %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0  (%color_debug% %+ echo folder.jpg is the same as cover.jpg, so deleting.                  %+ %color_removal% %+        *del folder.jpg           ))
     if exist folder.gif .and. exist cover.gif   (%color_run% %+ echos %ITALICS_ON% %+ comp folder.gif cover.gif  %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0  (%color_debug% %+ echo folder.gif is the same as cover.gif, so deleting.                  %+ %color_removal% %+        *del folder.gif           ))
     if exist folder.png .and. exist cover.png   (%color_run% %+ echos %ITALICS_ON% %+ comp folder.png cover.png  %+ echos %ITALICS_OFF% %+ if %ERRORLEVEL% == 0  (%color_debug% %+ echo folder.png is the same as cover.png, so deleting.                  %+ %color_removal% %+        *del folder.png           ))

%color_normal%
:dir cover*


