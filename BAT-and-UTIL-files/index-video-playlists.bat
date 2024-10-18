@Echo ON

::::: DOCUMENTATION:
    :USAGE:   index-video-playlists [quick]
    :         Option 'quick' changes quickness such that indexing happens faster, but with less date/time-specific auto-playlists.
    :PURPOSE: Create M3u playlists for each video tag. Especially important: The "party" tag.
    :HISTORY: to do for videos what index-audio-playlists does for audio
    :         copied from index.bat from our pictures, forked off into this version 20110402 but did not do real development until 201506


rem Validate environment:
        call validate-in-path alarmbeep  create-symlinks-by_Letter_only go-to-video-repository.bat

::::: PROCESS COMMAND-LINE ARGUMENTS:
    if "%1" != "" (call alarmbeep %*Unknown first argument of: %1!! %+ pause %+ pause %+ goto :END)

::::: PREPARE:
    timer /1 on %+ set COLUMNS=%_COLUMNS
    call create-symlinks-by_Letter_only %*
    cls %+ call go-to-video-repository.bat nodir %+ if isdir LISTS cd LISTS

::::: GENERATE:
    color bright yellow on black %+ Echo * Generating attribute filelists... %+ color white on black %+ rem Next line: q3 removes date stuff
    if "%@UPPER[%1]" ne "QUICK" SET QUICKNESS=3
    if "%@UPPER[%1]" eq "QUICK" SET QUICKNESS=123
    call validate-environment-variable BAT
    generate-filelists-by-attribute.pl -q%QUICKNESS% -g -i%BAT%\generate-filelists-by-attribute-video.ini

::::: CLEANUP:
    call go-to-video-repository.bat nodir
    if isdir lists cd lists
    if isdir auto  cd auto
    timer /1 off

:END
