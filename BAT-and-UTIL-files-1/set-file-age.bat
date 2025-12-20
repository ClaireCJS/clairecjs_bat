@Echo OFF
@on break cancel

REM ***************** Get/Validate parameters *****************
        iff "" == "%1%" then
                echo.
                if defined color_advice %color_advice%
                echo         USAGE: %0 {filename}, where {filename} is the file you want to get the age of
                echo        OUTPUT:  sets %AGE% to %RESULT% which is %RESULT_IN_SECONDS% which is the file’s age in seconds
                if defined color_normal %color_normal%
                goto /i :END
        endiff



REM ***************** Get/Validate parameters *****************
        set  FILE=%1
        call validate-env-var FILE

REM ******************** Calculate the age ********************
             REM            SET SECONDS_PER_MINUTE=60
             SET              TIMESTAMP_PER_SECOND=10000000
             REM                                   ^^^^^^^^ 10,000,000 / 10M / ten million
             SET          SETFILEAGE__OUR_FILE_AGE=%@FILEAGE["%FILE%"     ]
             SET         SETFILEAGE__TIMESTAMP_NOW=%@MAKEAGE[%_date,%_time]
        REM  SET SETFILEAGE__REFRESH_THRESHOLD_MIN=%@EVAL[%MINUTES_BEFORE_REFRESH% * %SECONDS_PER_MINUTE% * %TIMESTAMP_PER_SECOND%]
             SET     SETFILEAGE__CURRENT_DELTA_VAL=%@EVAL[%SETFILEAGE__TIMESTAMP_NOW%            -      %SETFILEAGE__OUR_FILE_AGE%]
             SET     SETFILEAGE__CURRENT_DELTA_SEC=%@EVAL[%SETFILEAGE__CURRENT_DELTA_VAL%        /          %TIMESTAMP_PER_SECOND%]
        REM  SET     SETFILEAGE__CURRENT_DELTA_MIN=%@EVAL[%SETFILEAGE__CURRENT_DELTA_SEC%        /            %SECONDS_PER_MINUTE%]
        REM                        AGE_CHECK=INDEX=%@EVAL[%SETFILEAGE__CURRENT_DELTA_MIN%        >        %MINUTES_BEFORE_REFRESH%]

REM ********************** Set results **********************
        set RESULTS_LIST=RESULT_IN_SECONDS RESULT AGE 

        set         RESULT_IN_SECONDS=%SETFILEAGE__CURRENT_DELTA_SEC%
        set RESULT=%RESULT_IN_SECONDS%
        set    AGE=%RESULT%

        set           RESULTS_DESCRIPTION=age of file (in several environment variables)
        set RESULT_IN_SECONDS_DESCRIPTION=age in seconds of file %FILE%
        set            RESULT_DESCRIPTION=synonym of RESULT_IN_SECONDS
        set               AGE_DESCRIPTION=synonym of RESULT


:END

