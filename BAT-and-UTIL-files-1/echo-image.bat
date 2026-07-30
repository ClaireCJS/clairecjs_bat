@Echo off



rem CONFIG:
        set chafa_scale=2.1
        set chafa_global_options=--optimize=9 --work=9 --color-space=din99d
        set chafa_nonworking_symbols=imported  ugly        none
        set chafa_working_symbols=all  sextant narrow  legacy block      wedge inverted  quad braille ascii   extra   bad  geometric     alnum  half   solid space   dot vhalf hhalf border   diagonal alpha latin  stipple     ambiguous digit    technical                             wide %+ rem These were painstakingly evaluated and ranked subjectively vs lots of images


rem USAGE:
        iff "%1" == "" then
                %color_advice%
                echo.
                echo ✨ USAG:  echo-image `<`image_name`>` [test] 
                echo            %faint_on%(adding test tests ansi art with all the different types of symbols)%faint_off%
                %color_normal%
        endiff

rem ENVIRONMENT VALIDATE (once):
        on break cancel
        iff "1" != "%validated_echoimage" then
                call validate-in-path chafa
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
        set chafa_view_size=--view-size=%@EVAL[%_COLUMNS * %chafa_scale]x%@EVAL[%_ROWS * %chafa_scale] 
        set chafa_rest=%chafa_global_options%  %chafa_file%  %chafa_command_tail%

rem RENDERING:
        iff     "1" == "%testing%" then                                        
                set chafa_scale=0.80
                set chafa_view_size=--view-size=%@EVAL[%_COLUMNS * %chafa_scale]x%@EVAL[%_ROWS * %chafa_scale] 
                for %%sym in (%chafa_working_symbols) (call divider %+ echo %bold_on%%blink_on%%sym%%blink_off%%bold_off%:  %+ chafa --format=symbols --symbols=%sym --colors=16/8 %chafa_view_size%    %chafa_rest% %+ pause>nul)
        elseiff "1" == "%CHAFA_ASCII_ART%" then 
                chafa --format=symbols --symbols=ascii --colors= 2                       %chafa_rest%
        elseiff "1" == "%CHAFA_ANSI_ART%" then                                            
                chafa --format=symbols --symbols=all   --colors=16/8                     %chafa_rest%
        else
echo            chafa --format=sixels  --fit-width     --colors=full %chafa_view_size%   %chafa_rest%
                chafa --format=sixels  --fit-width     --colors=full %chafa_view_size%   %chafa_rest%
        endiff