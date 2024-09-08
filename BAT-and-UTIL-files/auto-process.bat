@Echo On

call advice "Can run '%double_underline_on%%0 music%double_underline_off%' to force music-autoprocessing mode"

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
rem  GENERAL: Intended as a context-specific command to process files in general, but so far only used to process audio folders

rem  WHAT HAPPENS: It looks at the number of files of particular extensions [and later, will look at the folder name] to determine it's nature
rem                                  So far the only nature is to process audio folders

rem  For audio folder processing, it: 
rem             1) automatically opens up the current album/folder in Wikipedia & Discogs so that filenames can be renamed via text editor
rem             2) Deletes junk files
rem             3) moves metadata files into subfolder
rem             4) pulls artwork subfolders into main folder
rem             5) fixes file extensions
rem             6) standardizes namings of certain files (i.e. any cue files get renamed to cue.cue, any txt file get renamed to README.txt)
rem             7) interactively renames files in some cases
rem             8) opens certain files in text editor for review
rem             9) opens album art in album viewer for review
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

            
::::: VALIDATE ENVIRONMENT:
    call validate-in-path research-this-dir-on-discogs research-this-dir-on-wikipedia allfiles

::::: CONSTANTS:
    set TRIGGER_NAMED=__ already renamed __

::::: FLAGS:
    set    TO_ALLFILES=0 %+ REM //tracks whether we need to rename the current set of files or not
    set PROBABLY_MUSIC=0 %+ REM //gets flipped to 1 if we have flac or mp3 files, but also other times in scenarios that may not fully be tested
    set      WAS_MUSIC=0 %+ REM //currently only gets flipped to 1 in :music_FLAC_unconverted

::::: ANALYZE FOLDER CONTENTS:
    set COUNT_FLAC=%@FILES[*.flac] %+ if %COUNT_FLAC% gt 0 (set PROBABLY_MUSIC=1)
    set  COUNT_MP3=%@FILES[*.mp3]  %+ if %COUNT_MP3%  gt 0 (set PROBABLY_MUSIC=1)
    set  COUNT_WAV=%@FILES[*.wav]  %+ if %COUNT_WAV%  gt 0 (set PROBABLY_MUSIC=1)

::::: FIRST DETERMINE IF WE NEED TO RUN AN ALLFILES MV:  ** WHY ARE THESE LINES TRIPLED? IS THIS A BUG? WERE THEY SUPPOSED TO BE DIFFERENT? **
    if %COUNT_FLAC% gt 0 .and. %COUNT_MP3% eq 0 .and. %COUNT_WAV% eq 0 (set TO_ALLFILES=1)
    if %COUNT_FLAC% eq 0 .and. %COUNT_MP3% eq 0 .and. %COUNT_WAV% gt 0 (set TO_ALLFILES=1)
    if %COUNT_FLAC% eq 0 .and. %COUNT_MP3% gt 0 .and. %COUNT_WAV% eq 0 (set TO_ALLFILES=1)
    if exist "%TRIGGER_NAMED%"                                         (set TO_ALLFILES=0)

::::: COMMAND-LINE PARAMETER OVERRIDES:
    if "%1" eq "music" (set TO_ALLFILES=1 %+ set PROBABLY_MUSIC=1)

::::: NOW RUN AN ALLFILES MV IF THAT DETERMINATION WAS MADE:
     pushd .
    if "%DEBUG%" eq "" goto :NoDebug1
        %COLOR_DEBUG% %+ echo       - TO_ALLFILES: %TO_ALLFILES        
                         echo       - PROB_MUSIC_: %PROBABLY_MUSIC% 
        %COLOR_NORMAL%
    :NoDebug1
    if "%TO_ALLFILES%" ne "1" goto :NoRenamings
                if "%PROBABLY_MUSIC%" eq "1" (gosub :music_standardized_renamings)
                gosub :allfiles 
                goto  :END
    :NoRenamings


::::: BRANCH TO UTILITY FUNCTIONS (renamings already done, music_standardized_renamings already done if PROBABLY_MUSIC=1)
    :f %COUNT_FLAC% eq 0 .and. %COUNT_WAV% gt 0 (gosub branchDebug B %+ gosub :music_standardized_renamings %+ goto :END)  :: beta
    :f %COUNT_FLAC% gt 1 .and. %COUNT_MP3% eq 0 (gosub branchDebug A %+ gosub :music_FLAC_unconverted       %+ goto :END)  :: 20221117 commented out because we are allowing FLACs into our collection now
    if %COUNT_FLAC% gt 1 .or.  %COUNT_MP3% gt 1 .or.  %COUNT_WAV% gt 1 (gosub branchDebug C %+ gosub :music_standardized_renamings %+ goto :END)  :: for years, until 20221117


::::: IF WE GOT HERE, IT IS [CURRENTLY] AN ERROR INDICATING WE NEVER BRANCHED ANYWHERE ELSE:
    %COLOR_ALARM%  %+ echo. %+ echos * ERROR: Not sure how to process this folder, or processing already done. ``
    %COLOR_NORMAL% %+ echo. %+ echo.
    %COLOR_DEBUG%  %+ echo       - COUNT_FLAC: %@format[02,%COUNT_FLAC%]
    %COLOR_DEBUG%  %+ echo       - COUNT__MP3: %@format[02,%COUNT_MP3%]
    %COLOR_DEBUG%  %+ echo       - COUNT__WAV: %@format[02,%COUNT_WAV%]
    %COLOR_NORMAL% %+ echo. 
    %COLOR_DEBUG%  %+ echo       - PROB_MUSIC:  %PROBABLY_MUSIC%
    %COLOR_DEBUG%  %+ echo       - TO_ALLFILES: %TO_ALLFILES%



goto :END                                                                                           %+ REM skip subroutines
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :allfiles
            call research-this-dir-on-discogs
            call research-this-dir-on-wikipedia
            unset /q SWEEPING
            call allfiles mv
            call sleep 3
            >"%TRIGGER_NAMED%"
            dir
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :branchDebug [msg]
            %COLOR_DEBUG% %+ echo * [debug:Branch=%msg%] %+ %COLOR_NORMAL%
        return
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :music_Common
            %COLOR_ALARM% %+ echo (this does nothing right now) %+ %COLOR_NORMAL% %+ pause
        return
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :music_standardized_renamings
            :: debug
                if "%DEBUG%" eq "" goto :noDebug
                    %COLOR_DEBUG%  %+ echo *** music_standardized_renamings called, but skipping for debug purposes
                    %COLOR_NORMAL% %+ pause %+ return
                :noDebug

            :: delete b.s. files
                if exist *.ffp              ( del *.ffp             )
                if exist *.sfv              (*del *.sfv             )
                if exist *.m3u              (*del *.m3u             )
                if exist *.m3u8             (*del *.m3u8            )
                if exist delme*.*           (*del delme*.*          )
                if exist .[a-z0-9]*         ( del .[a-z0-9]*        )
                if exist ~uTorrentPartFile* ( del ~uTorrentPartFile*)

            :: save b.s. files
                set FILEMASK_BS_ALBUM_FILES=*.json;*spectrogram.png
                if exist %FILEMASK_BS_ALBUM_FILES% (md meta %+ mv %FILEMASK_BS_ALBUM_FILES% meta)

            :: collapse artwork in subfolders
                for %%zz in (art cover covers artwork artworks) if isdir "%zz" mv/ds "%zz" .

            :: fix stupid extensions
                if %@FILES[*.jpeg] gt 0 ren *.jpeg *.jpg
                if %@FILES[*.nfo]  gt 1 ren *.nfo  *.txt

            :: standard names for one-file-of-this-extension
                if %@FILES[*.accurip] eq 1 ren  *.accurip  accurip.log
                if %@FILES[*.cue]     eq 1 ren  *.cue          cue.cue
                if %@FILES[*.jpg]     eq 1 ren  *.jpg       folder.jpg
                if %@FILES[*.log]     eq 1 ren  *.log          eac.log
                if %@FILES[*.rtf]     eq 1 ren  *.rtf       README.rtf
                if %@FILES[*.txt]     eq 1 ren  *.txt       README.txt
    
            :: standard renamings for files with certain names:
                if not exist folder.jpg if exist cover.jpg ren cover.jpg folder.jpg
                if not exist folder.jpg if exist front.jpg ren front.jpg folder.jpg


            :: interactive renamings for multiple files with certain extensions:
                if %@FILES[*.log] gt 1 (color 4 on 14% %+ dir /b *.log %+ %COLOR_NORMAL %+ call rn *.log )
                if %@FILES[*.rtf] gt 1 (color 4 on 14% %+ dir /b *.rtf %+ %COLOR_NORMAL %+ call rn *.rtf )
                if %@FILES[*.cue] gt 1 (color 4 on 14% %+ dir /b *.cue %+ %COLOR_NORMAL %+ call rn *.cue )
                if %@FILES[*.txt] gt 1 (color 4 on 14% %+ dir /b *.txt %+ %COLOR_NORMAL %+ call rn *.txt )

            :: certain extensions, we want to load in our text editor:
                if %@FILES[*.cue] ge 1 (%EDITOR% *.cue)
                if %@FILES[*.log] ge 1 (%EDITOR% *.log)
                if %@FILES[*.nfo] ge 1 (%EDITOR% *.nfo)
                if %@FILES[*.rtf] ge 1 (%EDITOR% *.rtf)
                if %@FILES[*.txt] ge 1 (%EDITOR% *.txt)

            :: certain extensions, we want to load in other ways:
                if %@FILES[*.jpg] gt 1 (set FIRST_JPG=%@EXECSTR[ffind /k /b *.jpg | head -1] %+ "%FIRST_JPG%")

            :: and display our progress:
                echo. %+ echo. %+ echo. 
                dir
        return
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :music_FLAC_only_renamings
            echo.
							call warning "This shouldn't be happening because we are allowing FLAC files into our MP3 collection now. What gives?"
							pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ 
            dir
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :music_FLAC_unconverted
            set WAS_MUSIC=1
            rem 2022 Now that we are allowing FLAC files into our collection, there's no need to convert them, and this section is deprecated:
            rem gosub :music_FLAC_only_renamings

            call warning "This looks like a freshly-named FLAC album"

            :: collapse artwork in subfolders
                for %%zz in (art cover covers artwork artworks) if isdir "%zz" mv/ds "%zz" .

            rem :: convert to wav
            rem     if %@FILES[*.flac] gt %@FILES[*.wav] (call allfiles flac2wav)
            rem     cls
            rem     echo. %+ echo. %+ echo. %+ echo.
            rem     pause
            rem     %COLOR_NORMAL%
            rem     cls
            rem     dir
            rem     echo.
            rem     call warning "These names better look good!  Last chance to abort!"
            rem     pause
            rem :: segregate WAVs to separate folder
            rem     set       ALBUM_DIR_FLAC=%_CWD
            rem     set       ALBUM_DIR_BASE=%@NAME[%_CWD]
            rem     set       ALBUM_DIR_WAV=..\"%ALBUM_DIR_BASE%"
            rem     if exist %ALBUM_DIR_WAV% (set ALBUM_DIR_WAV=%ALBUM_DIR_WAV%.wav)
            rem     if exist %ALBUM_DIR_WAV% (echo *WTF*, %ALBUM_DIR_WAV% already exists aborting %+ pause %+ pause %+ beep %+ pause %+ goto :END)
            rem     md       %ALBUM_DIR_WAV%
            rem     set ALBUM_DIR_WAV_TRUENAME=%@TRUENAME[%ALBUM_DIR_WAV%]
            rem 
            rem     %COLOR_REMOVAL%
            rem     mv *.wav %ALBUM_DIR_WAV%
            rem     no *.flac cp * %ALBUM_DIR_WAV%
            rem     %COLOR_NORMAL%
            rem 
            rem :: create burn target dir
            rem     cd ..
            rem     set BAND_NAME_BASE="%@NAME[%_CWD]"
            rem     set MUSIC_BURN_DESTINATION_BASE=%DATA2%\MUSIC
            rem     set MUSIC_BURN_DESTINATION_BAND="%@UNQUOTE[%MUSIC_BURN_DESTINATION_BASE%]\%@UNQUOTE[%BAND_NAME_BASE%]"
            rem     if not isdir "%MUSIC_BURN_DESTINATION_BASE%" md /s "%@UNQUOTE[%MUSIC_BURN_DESTINATION_BASE%]"
            rem     if not isdir "%MUSIC_BURN_DESTINATION_BAND%" md /s "%@UNQUOTE[%MUSIC_BURN_DESTINATION_BAND%]"
            rem     call validate-environment-variables                            MUSIC_BURN_DESTINATION_BASE MUSIC_BURN_DESTINATION_BAND
            rem 
            rem :: move flac version to burn target dir
            rem     %COLOR_SUCCESS%
            rem      echo      mv/ds "%ALBUM_DIR_FLAC%" "%@UNQUOTE[%MUSIC_BURN_DESTINATION_BAND%]\%@UNQUOTE[%ALBUM_DIR_BASE%].flac"
            rem     (echo yryr|mv/ds "%ALBUM_DIR_FLAC%" "%@UNQUOTE[%MUSIC_BURN_DESTINATION_BAND%]\%@UNQUOTE[%ALBUM_DIR_BASE%].flac")
            rem     if isdir "%ALBUM_DIR_FLAC%" rd "%ALBUM_DIR_FLAC%"
            rem     %COLOR_NORMAL%
            rem 
            rem :: files to delete if present:
            rem     if exist "WHOLE ALBUM.wav" del "WHOLE ALBUM.WAV"
            rem 
            rem :: go to the finished folder (so we are in good position to use 'nd' to go to next dir)
            rem     "%@UNQUOTE[%ALBUM_DIR_WAV_TRUENAME%]\"
            rem 
            rem :: report that we are done:
            rem     echo. %+ echo. %+ echo. %+ echo.
            rem     dir
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
 :might not be relevant anymore: popd >nul
 unset /q SWEEPING

