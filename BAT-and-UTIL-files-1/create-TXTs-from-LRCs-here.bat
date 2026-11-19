@Echo OFF


rem Validate environment (once):
        iff "1" != "%validated_CreateTXTFromLRCsHereBAT%" then
                if not defined ANSI_COLORS_HAVE_BEEN_SET call set-ansi force
                if not defined FILEMASK_AUDIO call validate-environment-variable FILEMASK_AUDIO skip_existence_check
                call validate-in-path lrc2txt set-ansi repeat
                set validated_CreateTXTFromLRCsHereBAT=1
        endiff


rem Do it:
for %%tmpaudiofile in (%FILEMASK_AUDIO%) do if exist "%@NAME[%tmpaudiofile%].lrc" .and. not exist "%@NAME[%tmpaudiofile%].txt" (repeat 4 echo. %+ echo %ansi_color_less_important%%STAR2% Has %italics_on%LRC%italics_off% but no %italics_on%TXT%italics_off%: %faint_on%%tmpaudiofile%%faint_off%: %+ call lrc2txt "%@NAME[%tmpaudiofile%].lrc")

