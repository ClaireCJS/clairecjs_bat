@loadbtm on
@Echo OFF
 on break cancel


rem Halt condition:
        if not exist *.srt (echo %ansi_color_unimportant%%star2% No bad files to delete%ansi_color_normal% %+ goto :END)

rem Validate environment (once):
        iff 1 ne %validated_dbaitr% then
                call validate-in-path grep insert-before-each-line.py insert-after-each-line.py run-piped-input-as-bat.bat
                set  validated_dbaitr=1
        endiff

rem Do it:
        call set-tmp-file "kill bad AI transcriptions"                                        
        grep -li and.we.are.back *.srt >%tmpfile
        type %tmpfile% |:u8 insert-before-each-line.py "*del /Ns {{{{QUOTE}}}}{{{{PERCENT}}}}@name[" |:u8 insert-after-each-line.py "].txt{{{{QUOTE}}}}" ) |:u8 run-piped-input-as-bat
        type %tmpfile% |:u8 insert-before-each-line.py "*del /Ns {{{{QUOTE}}}}{{{{PERCENT}}}}@name[" |:u8 insert-after-each-line.py "].log{{{{QUOTE}}}}" ) |:u8 run-piped-input-as-bat
        type %tmpfile% |:u8 insert-before-each-line.py "*del /Ns {{{{QUOTE}}}}{{{{PERCENT}}}}@name[" |:u8 insert-after-each-line.py "].srt{{{{QUOTE}}}}" ) |:u8 run-piped-input-as-bat

rem Of course this opens a new issue which is.... If any lyric to ay song is LEGITIMATELY "and we are back" ... we’re in trouble.

:END
