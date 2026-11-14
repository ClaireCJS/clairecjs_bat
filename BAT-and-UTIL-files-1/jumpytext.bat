@echo off


set DEFAULT_METHOD=6
set DEFAULT_DELAYTIME=60



rem Get method:
        set method=%DEFAULT_METHOD%
        iff "%1" != "" then
                set method=%1
                shift
        endiff

rem Get delaytime:
        set delaytime=%DEFAULT_DELAYTIME%
        iff "%1" != "" then
                set delaytime=%1
                shift
        endiff

rem Do it:
        gosub %method%
        goto :END



rem Subroutines:
        :1
                send_mousewheel_input.exe up   3 %delaytime%
                send_mousewheel_input.exe down 6 %delaytime%
                send_mousewheel_input.exe up   3 %delaytime%
        return


        :2
                send_mousewheel_input.exe down 1 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   1 %delaytime%
        return

        :3
                send_mousewheel_input.exe up   1 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 1 %delaytime%
        return


        :4
                send_mousewheel_input.exe up   1 %delaytime%
                send_mousewheel_input.exe down 1 %delaytime%
                send_mousewheel_input.exe up   1 %delaytime%
                send_mousewheel_input.exe down 1 %delaytime%
                send_mousewheel_input.exe up   1 %delaytime%
                send_mousewheel_input.exe down 1 %delaytime%
        return

        :5
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
                send_mousewheel_input.exe up   2 %delaytime%
                send_mousewheel_input.exe down 2 %delaytime%
        return

        :6
                send_mousewheel_input.exe down 1 %delaytime%
                send_mousewheel_input.exe up   1 %delaytime%
                send_mousewheel_input.exe down 1 %delaytime%
                send_mousewheel_input.exe up   1 %delaytime%
                send_mousewheel_input.exe down 1 %delaytime%
                send_mousewheel_input.exe up   1 %delaytime%
        return


:END