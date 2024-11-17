@Echo OFF

call validate-in-path fix-unicode-filenames

rem ARE WE DOING THIS, OR JUST SAYING HOW TO DO IT?:
        if "%1" eq "go" (goto :Begin)
        if "%1" eq ""   (goto :Usage) %+ rem 20240324: Purposefully breaking all past invocations to this script in order to add the "go" safety in order to allow blank calls to be requests to display the usage
        if "%1" eq "/h" .or. "%1" eq "-h" .or. "%1" eq "--h" .or. "%1" eq "--help" .or. "%1" eq "/?" .or. "%1" eq "-?" .or. "%1" eq "?" .or. "%1" eq "help" (goto :usage)
        goto :Begin
        :Usage
            %COLOR_ADVICE%
                echo.
                echo %bold%%underline%USAGE%underline_off%:%bold_off% %italics_on%%0 go   %italics_off%—— does a generic %emphasis%allfiles mv%deemphasis%, but in %blink_on%automatic mode%blink_off%. 
                echo                         %italics%May take folder location into account.%italics_off%
                echo.
                echo %bold%%underline%USAGE%underline_off%:%bold_off% %italics_on%%0 rmaa %italics_off%—— Like '%italics%%0 go%italics_off%', but strips "%italics_on%Artist - Album Title - %italics_off%" from each filename beginning.  %blink%For music.%blink_off%
                echo                         %italics%Takes parent + grandparent folder names into account.%italics_off%
            %COLOR_NORMAL%
        goto :END


rem PARAMETER PROCESSING:
        :Begin
        SET NOEXIF=0
        ::if "%@UPPER[%1]" eq "AFTER"  (goto  :After)
          if "%@UPPER[%1]" eq "rmaa"   (SET REMOVE_ARTIST_ALBUM_FROM_FILENAME_MODE=1) %+ rem affects allfilesmv.pl
          if "%@UPPER[%1]" eq "NOEXIF" (SET NOEXIF=1)

rem SPECIAL STUFF FOR EXIF-EXTRACTION & NEWPICS ONLY:
        rem TODO CHECK IF WE ARE IN DROPBOX AND IF FILES START WITH P1000876.jpg P???????.jpg THEN it is the new camera
        rem  set prefix name to folder name - eset it - then rename with the prefixing
        if %NOEXIF eq 1 (goto :NoExif)
            if %@REGEX[%@UPPER[newpics],%@UPPER[%_CWP]]== 0 (goto :NotNewPics)
                            set DONE_EXIF_TRIGGER=__ done - allfiles exif time __
                            if exist "%DONE_EXIF_TRIGGER%"  (goto :SkipAllfilesExif)
                                    call allfiles exif time
                                    >"%DONE_EXIF_TRIGGER%"
                            :SkipAllfilesExif
            :NotNewPics
        :NoExif

rem But let's fix the unicode filenames first...
        call fix-unicode-filenames auto

rem RUN "ALLFILES MV" (with %SWEEPING% having been set to 1 to trigger automatic mode):
        set  SWEEPING_TEMP=%SWEEPING%
        set  SWEEPING=1
        set  NOPAUSE_TEMP=%NOPAUSE%
        set  NOPAUSE=1
        call allfiles mv %+ rem will honor %REMOVE_ARTIST_ALBUM_FROM_FILENAME_MODE% and change behavior as such
        set  SWEEPING=%SWEEPING_TEMP%
        set  NOPAUSE=%NOPAUSE_TEMP%

rem POSSIBLE FUTURE IDEA: workflow-related automatic reactions to a freshly-named folder:
        ::   :After
        ::   call autoprocess

:END

rem Cleanup:
        if defined REMOVE_ARTIST_ALBUM_FROM_FILENAME_MODE (set REMOVE_ARTIST_ALBUM_FROM_FILENAME_MODE=)


