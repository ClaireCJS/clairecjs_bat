@loadbtm on
@Echo OFF
@on break cancel

rem CONFIG:
        set TRIGGER_FILE=.GetAllLRCsRunHereAlready %+ rem This filename must also be an entry in clean-up-AI-transcription-trash-files-everywhere.bat


rem Validate environment:
        if not defined filemask_audio call validate-environment-variable filemask_audio
        iff "1" != "%validated_getalllrcs%" then
                call validate-in-path get-lrc.bat
                call validate-environment-variables ansi_colors_have_been_set emoji_have_been_set
                set validated_getalllrcs=1
        endiff


rem Unset this flag because it’s only applicable mid-run:
        unset /q SKIPPING_GET_LRCS_FOR_REST_OF_FOLDER

rem Don’t run if we’ve already run here:
        iff exist %TRIGGER_FILE% .and. "%1" != "force" .and. "%1" != "/f" .and. "%1" != "--force" then
                echo %ANSI_COLOR_SOFT_WARNING%%EMOJI_STOP_SIGN% %bold_on%%underline_on%Skipping%underline_off%:%bold_off% already ran %italics_on%get-all-LRCs%italics_off% here
                goto :END_OF_GET_ALL_LRCs
        endiff

rem Skip doing anything if there are no files of appropriate extension
        iff not exist %FILEMASK_VOCAL% then
                call warning_soft "No files of proper format here"
                goto /i :trigger_getalllrcs
        endiff


rem Run Get-LRC on all audio files:
        rem Anti-message dancing invocation:
                set MESSAGE_DANCING=0
                set MESSAGE_SILENCE=1

        rem Actually run Get-LRC on all files:
                for %getalllrcstmpfile in (%FILEMASK_AUDIO%) do if "1" != "%SKIPPING_GET_LRCS_FOR_REST_OF_FOLDER%" call get-lrc "%@UNQUOTE["%getalllrcstmpfile%"]"
                unset /q SKIPPING_GET_LRCS_FOR_REST_OF_FOLDER

        rem Restore message dancing state:
                set MESSAGE_DANCING=1
                set MESSAGE_SILENCE=0


rem Leave breadcrumb that we’ve now run this here:
        :trigger_getalllrcs
        >%TRIGGER_FILE%



:END_OF_GET_ALL_LRCs
