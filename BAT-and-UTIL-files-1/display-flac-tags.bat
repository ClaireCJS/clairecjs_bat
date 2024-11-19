@on break cancel
@Echo OFF

rem Config:
        set EXCEPT_BLOCK_TYPE=PICTURE,PADDING,SEEKTABLE
        %COLOR_ADVICE% %+ echos * Block types of %EXCEPT_BLOCK_TYPE% will not be displayed.
        %COLOR_NORMAL% %+ echo.


rem Environment validation:
        iff 1 ne %VALIDATED_DFLT% then
                call validate-in-path               metaflac fast_cat
                call validate-environment-variables ansi_color_magenta ansi_color_normal color_advice color_normal
                set  VALIDATED_DFLT=1
        endiff


rem Parameters:
        set  DFLACPARAMS=%*
        if "%DFLACPARAMS%" eq "*" (set DFLACPARAMS=*.flac)


rem DO IT!
        iff 1 ne %DISPLAY_TAGS_PREFIX_NAME% then
                metaflac  --list  --except-block-type=%EXCEPT_BLOCK_TYPE%   %DFLACPARAMS% 
        else
               (metaflac  --list  --except-block-type=%EXCEPT_BLOCK_TYPE%   %DFLACPARAMS% |:u8 insert-before-each-line "%ansi_color_magenta%%@UNQUOTE[%1$]:%ansi_color_normal%" ) |:u8 fast_cat
        endiff
        

