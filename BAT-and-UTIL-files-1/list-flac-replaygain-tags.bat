@echo off
@on break cancel

rem Validate environment (once):
        iff "1" != "%validated_listreplaygaintags%" then
                call validate-in-path metaflac grep set-tmp-file type
                if not defined ansi_has_been_set call validate-environment-variable ansi_has_been_set
                set  validated_listreplaygaintags=1
        endiff

rem Set tmp file for results:
        call set-tmp-file

rem Flesh out all our replaygain tags:
        (metaflac --list *.flac|:u8grep -i replaygain_track_gain) >:u8 %tmpfile1%

rem Count how many files we have, and how many results we have:
        set COUNT_FLAC=%@FILES[*.flac]
        set COUNT_REPLAYGAIN=%@INC[%@LINES[%tmpfile1%]]

rem Compute compliance rate
        set COMPLIANCE_RATE=%@FLOOR[%@eval[%COUNT_REPLAYGAIN% / %COUNT_FLAC% * 100]]

rem Compuate how to color and display the compliance rate:
        if %COMPLIANCE_RATE% ge 100 set COMPLIANCE_COLOR=%ansi_color_bright_green%
        if %COMPLIANCE_RATE% lt 100 set COMPLIANCE_COLOR=%ansi_color_bright_yellow%
        if %COMPLIANCE_RATE% lt  90 set COMPLIANCE_COLOR=%ansi_color_bright_red%
        iff "%COUNT_REPLAYGAIN%" == "0" then
                set punctuation_to_use=%ansi_color_bright_red%!
        else
                set punctuation_to_use=:
        endiff

rem Show it on the screen, with summary:
        echo %faint_off%%ANSI_COLOR_IMPORTANT%%STAR% %bold_on%%blink_on%%COUNT_REPLAYGAIN%%blink_off%%bold_off% %faint_on%of%faint_off% %bold_on%%COUNT_FLAC%%bold_off% %faint_on%(%faint_off%%bold_on%%COMPLIANCE_COLOR%%compliance_rate%%bold_off%%@CHAR[65285]%ansi_color_important%%faint_on%) %italics_on%FLAC%italics_off% files have tags%punctuation_to_use%%ANSI_COLOR_NORMAL%
        type %tmpfile% |:u8 insert-before-each-line "      %faint_on%"


if "%COMPLIANCE_COLOR%" != "%ansi_color_bright_green%" (echos           `` %+ call warning "%italics_on%ReplayGain%italics_off% compliance is %ansi_color_bright_red%NOT%ansi_color_warning% established")
