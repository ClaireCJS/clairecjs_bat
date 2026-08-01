@Echo off



rem CONFIG:
        set echoimage_chafa=chafa-1.18.2.exe
        set chafa_scale=1.9
        set chafa_reserved_text_rows=2
        set chafa_global_options=--optimize=9 --work=9 --color-space=din99d
        set chafa_nonworking_symbols=imported  ugly        none
        set chafa_working_symbols=all  sextant narrow  legacy block      wedge inverted  quad braille ascii   extra   bad  geometric     alnum  half   solid space   dot vhalf hhalf border   diagonal alpha latin  stipple     ambiguous digit    technical                             wide %+ rem These were painstakingly evaluated and ranked subjectively vs lots of images


rem USAGE:
        iff "%1" == "" then
                %color_advice%
                echo.
                echo ✨ USAGE:  echo-image `<`image_name`>` [test] 
                echo            %faint_on%(adding test tests ansi art with all the different types of symbols)%faint_off%
                %color_normal%
        endiff

rem ENVIRONMENT VALIDATE (once):
        on break cancel
        iff "1" != "%validated_echoimage" then
                call validate-in-path chafa %echoimage_chafa% "we need a chafa-1.18.2.exe specifically for future stability"
                set  validated_echoimage=1
        endiff


rem PARAMETER FETCH:
        set chafa_file=%1
        shift
        iff "%1" == "test" then
                set testing=1
                shift
        else
                set testing=0                                   
        endiff
        set chafa_command_tail=%1$

rem PARAMETER VALIDATE:
        if not exist %chafa_file% call validate-environment-variable chafa_file


rem GLOBAL OPTIONS:
        rem Query this terminal's live cells and font pixels, then fit both axes.
        rem chafa_view_size=%@EXECSTR[python -m clairecjs_utils.claire_terminal_geometry --format chafa --reserve-rows %chafa_reserved_text_rows] --scale=max
        set COLS=%_COLUMNS
        set ROWS=%_ROWS
        set chafa_view_size=--view-size=%COLS%x%ROWS% --scale=max 
        set chafa_rest=%chafa_global_options%  %chafa_file%  %chafa_command_tail%

rem RENDERING:
        unset /q last_chafa_command
        iff     "1" == "%testing%" then                                        
                set chafa_scale=0.80
                set chafa_view_size=--view-size=%@EVAL[%_COLUMNS * %chafa_scale]x%@EVAL[%_ROWS * %chafa_scale] 
                for %%sym in (%chafa_working_symbols) (call divider %+ echo %bold_on%%blink_on%%sym%%blink_off%%bold_off%:  %+ %echoimage_chafa% --format=symbols --symbols=%sym --colors=16/8 %chafa_view_size%    %chafa_rest% %+ pause>nul)
        elseiff "1" == "%CHAFA_ASCII_ART%" then 
                set LAST_CHAFA_COMMAND=%echoimage_chafa%  --format=symbols  --colors= 2    --symbols=ascii     %chafa_rest%
        elseiff "1" == "%CHAFA_ANSI_ART%" then                                              
                set LAST_CHAFA_COMMAND=%echoimage_chafa%  --format=symbols  --colors=16/8  --symbols=all       %chafa_rest%
        else                                                                                
                set LAST_CHAFA_COMMAND=%echoimage_chafa%  --format=sixels   --colors=full  %chafa_view_size%   %chafa_rest%
                set LAST_CHAFA_COMMAND=%echoimage_chafa%  --format=sixels   --colors=full                      %chafa_rest% --margin-bottom=3 --margin-right=0 
                set LAST_CHAFA_COMMAND=%echoimage_chafa%  --format=sixels   --colors=full  %chafa_view_size%   %chafa_rest% --margin-bottom=4 --margin-right=0 
        endiff
        iff defined LAST_CHAFA_COMMAND then
                %LAST_CHAFA_COMMAND%
                rem DEBUG: 
                echo %ansi_color_debug%LAST_CHAFA_COMMAND=%LAST_CHAFA_COMMAND%%ansi_color_normal%
        endiff