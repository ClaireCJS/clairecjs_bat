@Echo OFF

rem Sets a tag to associate with a file, using Windows Alternate Data Streams for files. 
rem These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn't change things.

rem Get parameters:
        set  OUR_FILE_TO_TAG=%@UNQUOTE[%1]                                              %+ rem Lyric file to use 
        set ALERNATE_METATAG=%2                                                         %+ rem to allow us to specify a tag, including UN-approving, or anything else
        set ALERNATE_METAVAL=%3                                                         %+ rem to allow us to specify a value, for aforementioned custom tag

rem Set default values for parameters:
        if "%ALTERNATE_METATAG%" eq "" (set ALTERNATE_METATAG=lyrics)
        if "%ALTERNATE_METAVAL%" eq "" (set ALTERNATE_METATAG=approve)


rem Validate environment and parameter:
        call validate-environment-variable OUR_FILE_TO_TAG "First arg must be a lyric file. 2ⁿᵈ optional arg can be a tag other than 'lyrics' to add to file, 3ʳᵈ can be a value other than approved/not_approved/etc to add to file"
        call validate-extension            OUR_FILE_TO_TAG *.txt;*.srt;*.lrc            %+ rem 👟 We will also sneak subtitles in, in case we decide to add approval for those down the road

rem Set via windows alternate data streams:
        echo %ALTERNATE_METAVAL%>%OUR_FILE_TO_TAG%:%ALTERNATE_METATAG%


