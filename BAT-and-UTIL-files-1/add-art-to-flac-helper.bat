@Echo OFF

rem Validate the environment:
        if %VALIDATE_ADDARTTOFLAC ne 1 (
            call validate-in-path metaflac warning success error
            set VALIDATE_ADDARTTOFLAC=1
        )
         unset /q ART
         unset /q MUSIC
         unset /q VERB
         unset /q REMOVE_ART_FROM_FLAC

rem Are we adding art, or removing it? This changes our parameters and how we validate them... [Will probably fail on filenames with percent signs]

         if "%2" ne "REMOVE" .and. "%3" ne "REMOVE" (set REMOVE_ART_FROM_FLAC=0)
         if "%2" eq "REMOVE" .or.  "%2" eq "REMOVE" (set REMOVE_ART_FROM_FLAC=1)
         call print-if-debug  "REMOVE_ART_FROM_FLAC is '%REMOVE_ART_FROM_FLAC%'"

         if %REMOVE_ART_FROM_FLAC eq 1 (
                set             VERB=%ANSI_COLOR_REMOVAL%removed%ANSI_COLOR_RESET%
                set            MUSIC=%1
                set  ARTWORK_COMMAND=--remove --block-type=PICTURE %MUSIC% 
                call validate-environment-variable MUSIC 
                unset /q ART
         )
         if %REMOVE_ART_FROM_FLAC ne 1 (
                set             VERB=embedded
                set              ART=%1
                set            MUSIC=%2
                set  ARTWORK_COMMAND=--import-picture-from="%@UNQUOTE[%ART]" %MUSIC% 
                call validate-environment-variables  ART   MUSIC
                call validate-file-extension        %ART% %FILEMASK_IMAGE%
         )  
         call print-if-debug "verb='%verb%',art='%art%',music='%music%'"
         call validate-file-extension %MUSIC% %FILEMASK_AUDIO%


rem Run the command!
         echos %ANSI_COLOR_DEBUG%%STAR%
         echo  metaflac %ARTWORK_COMMAND% %ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_COLOR_RUN%
               metaflac %ARTWORK_COMMAND%
        call print-if-debug "this has now been fairly well tested for flac files, and fyi ERRORLEVEL == '%ERRORLEVEL%'"


rem Check if there was an error, and delete the artwork file if there wasn't:
        if ERRORLEVEL 1 (call error "embedding art '%ART%' into song '%SONG%' failed?! ")
        if ERRORLEVEL 0 .and. %DONT_DELETE_ART_AFTER_EMBEDDING ne 1 (
            call success "Art %italics_on%%VERB%%italics_off%" 

            if %DONT_DELETE_ART_AFTER_EMBEDDING ne 1 .and. exist %ART% .and. %REMOVE_ART_FROM_FLAC ne 1 (
                    echos  %ANSI_COLOR_REMOVAL%%ANSI_STRIKETHROUGH_ON%%FAINT_ON%
                    del /p %ART%
                    echos  %ANSI_RESET%
            )
        )
        unset /q REMOVE_ART_FROM_FLAC
