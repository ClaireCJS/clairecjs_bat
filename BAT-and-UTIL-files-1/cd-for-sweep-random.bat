@LoadBTM ON
@Echo OFF


rem This is just a change-directory with announce...


        rem Change directory:
                *cd %*

        rem Announce:
                                   echo %ansi_color_important%%STAR1% Running in: %ansi_color_important_less%%[italics_on]%[_CWD]%[italics_off]%faint_off%:%faint_off%%ansi_color_normal%
                if defined command echo %ansi_color_important%%zzz%      command: %ansi_color_important_less%%[italics_on]%faint_on%%@UNQUOTE["%sweep_command%"]%faint_off%%[italics_off]%ansi_color_normal%

