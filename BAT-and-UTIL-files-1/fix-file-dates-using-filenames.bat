@on break cancel
@echo off
 echo.


::::: CONFIGURATION:
    set DEBUG=0                                              %+ REM set to 1 to just echo touch commands
    set HIY=2100                                             %+ REM a "high year", realistically, a year that this script will probably not be used anymore
    set BREADCRUMB="__ dates fixed as of this date __"

::::: CHECK INVOCATION:
    if ""  ==   "%1"          (gosub :Usage    %+                                               %+ goto :END)
    if not exist %1           (%COLOR_WARNING% %+ echo * WARNING: DOES NOT EXIST: %1            %+ goto :END)
    if     exist %BREADCRUMB% (%COLOR_WARNING% %+ echo * Warning: We've already done this here. %+ if "%2" == "override" goto :DoIt %+ goto :END)

::::: DEBUG CONSIDERATIONS:
    if defined DEBUGECHO (unset /q DEBUGECHO     )
    if "%DEBUG%" == "1"  (  set    DEBUGECHO=echo)

::::: CYCLE THROUGH EACH FILE:
    :DoIt
    set FILES_TO_CHECK=%1
    for %zq in (%FILES_TO_CHECK%) gosub ProcessFile "%zq%"
goto :CleanUp


    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :ProcessFile [file]
        :: initialize
            %COLOR_IMPORTANT% %+ echo - Processing file: %file% %+ %COLOR_DEBUG%
            unset /q XX*

        :: grow the ability to see if it matches a pattern
            set FOLDERNAME_TRIED=0                          %+ REM For later: If the filename we are CHECKING_IN has no matches, we will then look in the folder name. This variable is used to track that state.
            set CHECKING_IN="%file%"
            :CheckMatches
            ::[1] YYYYMMDD HHmm
                set XX00=%@REGEXSUB[0,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX00: "%XX00%"
                set XX01=%@REGEXSUB[1,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX01: "%XX01%"
                set XX02=%@REGEXSUB[2,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX02: "%XX02%"
                set XX03=%@REGEXSUB[3,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX03: "%XX03%"
                set XX04=%@REGEXSUB[4,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX04: "%XX04%"
                set XX05=%@REGEXSUB[5,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX05: "%XX05%"
                set XX06=%@REGEXSUB[6,"([12][8901][0-9][0-9])([01][0-9])([0-3][0-9]) ([012][0-9])([0-5][0-9])",%CHECKING_IN%] %+ echo      - XX06: "%XX06%"
            ::[2] YYYY-MM-DD
                set XX10=%@REGEXSUB[0,"([12][8901][0-9][0-9])[\-_]*([01][0-9])[\-_]*([0-3][0-9])[^0-9]",%CHECKING_IN%]        %+ echo      - XX10: "%XX10%"
                set XX11=%@REGEXSUB[1,"([12][8901][0-9][0-9])[\-_]*([01][0-9])[\-_]*([0-3][0-9])[^0-9]",%CHECKING_IN%]        %+ echo      - XX11: "%XX11%"
                set XX12=%@REGEXSUB[2,"([12][8901][0-9][0-9])[\-_]*([01][0-9])[\-_]*([0-3][0-9])[^0-9]",%CHECKING_IN%]        %+ echo      - XX12: "%XX12%"
                set XX13=%@REGEXSUB[3,"([12][8901][0-9][0-9])[\-_]*([01][0-9])[\-_]*([0-3][0-9])[^0-9]",%CHECKING_IN%]        %+ echo      - XX13: "%XX13%"
                set XX14=%@REGEXSUB[4,"([12][8901][0-9][0-9])[\-_]*([01][0-9])[\-_]*([0-3][0-9])[^0-9]",%CHECKING_IN%]        %+ echo      - XX14: "%XX14%"
            ::[3] YYYYMM
                set XX20=%@REGEXSUB[0,"([12][8901][0-9][0-9])([01][0-9])",%CHECKING_IN%]                                      %+ echo      - XX20: "%XX20%"
                set XX21=%@REGEXSUB[1,"([12][8901][0-9][0-9])([01][0-9])",%CHECKING_IN%]                                      %+ echo      - XX21: "%XX21%"
                set XX22=%@REGEXSUB[2,"([12][8901][0-9][0-9])([01][0-9])",%CHECKING_IN%]                                      %+ echo      - XX22: "%XX22%"
                set XX23=%@REGEXSUB[3,"([12][8901][0-9][0-9])([01][0-9])",%CHECKING_IN%]                                      %+ echo      - XX23: "%XX23%"
            ::[6] 1960s (early|mid|late)
                set XX35=%@REGEXSUB[0,"([12][8901][0-9])0s \(([^\)]*)\)",%CHECKING_IN%]                                       %+ echo      - XX35: "%XX35%"
                set XX36=%@REGEXSUB[1,"([12][8901][0-9])0s \(([^\)]*)\)",%CHECKING_IN%]                                       %+ echo      - XX36: "%XX36%"
                set XX37=%@REGEXSUB[2,"([12][8901][0-9])0s \(([^\)]*)\)",%CHECKING_IN%]                                       %+ echo      - XX37: "%XX37%"
                set XX38=%@REGEXSUB[3,"([12][8901][0-9])0s \(([^\)]*)\)",%CHECKING_IN%]                                       %+ echo      - XX38: "%XX38%"
            ::[7] 1960s 
                set XX45=%@REGEXSUB[0,"([12][8901][0-9])0s - ",%CHECKING_IN%]                                                 %+ echo      - XX45: "%XX45%"
                set XX46=%@REGEXSUB[1,"([12][8901][0-9])0s - ",%CHECKING_IN%]                                                 %+ echo      - XX46: "%XX46%"
                set XX47=%@REGEXSUB[2,"([12][8901][0-9])0s - ",%CHECKING_IN%]                                                 %+ echo      - XX47: "%XX47%"
                set XX48=%@REGEXSUB[3,"([12][8901][0-9])0s - ",%CHECKING_IN%]                                                 %+ echo      - XX48: "%XX48%"
            ::[4] 1800s (early|mid|late)
                set XX25=%@REGEXSUB[0,"([12][8901])00s \(([^\)]*)\)",%CHECKING_IN%]                                           %+ echo      - XX25: "%XX25%"
                set XX26=%@REGEXSUB[1,"([12][8901])00s \(([^\)]*)\)",%CHECKING_IN%]                                           %+ echo      - XX26: "%XX26%"
                set XX27=%@REGEXSUB[2,"([12][8901])00s \(([^\)]*)\)",%CHECKING_IN%]                                           %+ echo      - XX27: "%XX27%"
                set XX28=%@REGEXSUB[3,"([12][8901])00s \(([^\)]*)\)",%CHECKING_IN%]                                           %+ echo      - XX28: "%XX28%"
            ::[8] \YYYY[ish]\
                set XX80=%@REGEXSUB[0,"\\([12][8901][0-9][0-9])i*s*h*\\",%CHECKING_IN%]                                       %+ echo      - XX80: "%XX80%"
                set XX81=%@REGEXSUB[1,"\\([12][8901][0-9][0-9])i*s*h*\\",%CHECKING_IN%]                                       %+ echo      - XX81: "%XX81%"
                set XX82=%@REGEXSUB[2,"\\([12][8901][0-9][0-9])i*s*h*\\",%CHECKING_IN%]                                       %+ echo      - XX82: "%XX82%"
            ::[5] YYYY[ish] - 
                set XX30=%@REGEXSUB[0,"([12][8901][0-9][0-9])i*s*h* *-[^0-9]",%CHECKING_IN%]                                  %+ echo      - XX30: "%XX30%"
                set XX31=%@REGEXSUB[1,"([12][8901][0-9][0-9])i*s*h* *-[^0-9]",%CHECKING_IN%]                                  %+ echo      - XX31: "%XX31%"
                set XX32=%@REGEXSUB[2,"([12][8901][0-9][0-9])i*s*h* *-[^0-9]",%CHECKING_IN%]                                  %+ echo      - XX32: "%XX32%"
            ::[9] \1970-1979\MISC
                set XX90=%@REGEXSUB[0,"\\([12][8901][0-9])[0-9]-[12][8901][0-9][0-9]\\",%CHECKING_IN%]                        %+ echo      - XX90: "%XX90%"
                set XX91=%@REGEXSUB[1,"\\([12][8901][0-9])[0-9]-[12][8901][0-9][0-9]\\",%CHECKING_IN%]                        %+ echo      - XX91: "%XX91%"
                set XX92=%@REGEXSUB[2,"\\([12][8901][0-9])[0-9]-[12][8901][0-9][0-9]\\",%CHECKING_IN%]                        %+ echo      - XX92: "%XX92%"


        :: see if it maches a pattern
            unset /q NEW_HH
            unset /q NEW_MIN
            if %@LEN[%XX00%] == 13 .and. %@LEN[%XX01%]==4 .and. %@LEN[%XX02%] == 2 .and. %@LEN[%XX03%]==2 .and. %@LEN[%XX04%]==2 .and. %@LEN[%XX05%]==02 .and. %@LEN[%XX06%]  == 00                (echos [1] %+ set NEW_YYYY=%XX01%   %+ set NEW_MM=%XX02% %+ set NEW_DD=%XX03% %+ set NEW_HH=%%XX04% %+ set NEW_MIN=%XX05% %+                                                                                                 %+ goto :Match_YES)
            if %@LEN[%XX10%] gt 07 .and. %@LEN[%XX11%]==4 .and. %@LEN[%XX12%] == 2 .and. %@LEN[%XX13%]==2 .and. %@LEN[%XX14%]==0 .and. %XX11% lt %HIY% .and. %XX12% lt 13                          (echos [2] %+ set NEW_YYYY=%XX11%   %+ set NEW_MM=%XX12% %+ set NEW_DD=%XX13% %+ set NEW_HH=12      %+ set NEW_MIN=00     %+                                                                                                 %+ goto :Match_YES)
            if %@LEN[%XX20%] == 06 .and. %@LEN[%XX21%]==4 .and. %@LEN[%XX22%] == 2 .and. %@LEN[%XX23%]==0 .and. %XX21% lt %HIY%                                                .and. %XX22% lt 13  (echos [3] %+ set NEW_YYYY=%XX21%   %+ set NEW_MM=%XX22% %+ set NEW_DD=15     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+                                                                                                 %+ goto :Match_YES)
            if %@LEN[%XX35%] gt 07 .and. %@LEN[%XX36%]==3 .and. %@LEN[%XX37%] gt 2 .and. %@LEN[%XX38%]==0                                                                                          (echos [6] %+ set NEW_YYYY=%XX36%5  %+ set NEW_MM=01     %+ set NEW_DD=01     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+ if "%XX37%" == "early" (set NEW_YYYY=%XX36%2 ) %+ if "%XX37%" == "late" (set NEW_YYYY=%XX36%8 ) %+ goto :Match_YES)
            if %@LEN[%XX25%] gt 07 .and. %@LEN[%XX26%]==2 .and. %@LEN[%XX27%] gt 2 .and. %@LEN[%XX28%]==0                                                                                          (echos [4] %+ set NEW_YYYY=%XX26%50 %+ set NEW_MM=01     %+ set NEW_DD=01     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+ if "%XX27%" == "early" (set NEW_YYYY=%XX26%20) %+ if "%XX27%" == "late" (set NEW_YYYY=%XX26%80) %+ goto :Match_YES)
            if %@LEN[%XX45%] == 07 .and. %@LEN[%XX46%]==3 .and. %@LEN[%XX47%] == 0                                                                                                                 (echos [7] %+ set NEW_YYYY=%XX46%5  %+ set NEW_MM=01     %+ set NEW_DD=01     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+                                                                                                 %+ goto :Match_YES)
            if %@LEN[%XX30%] gt 03 .and. %@LEN[%XX31%]==4 .and. %@LEN[%XX32%] == 0                                                                                                                 (echos [5] %+ set NEW_YYYY=%XX31%   %+ set NEW_MM=06     %+ set NEW_DD=01     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+                                                                                                 %+ goto :Match_YES)
            if %@LEN[%XX80%] gt 05 .and. %@LEN[%XX81%]==4 .and. %@LEN[%XX82%] == 0                                                                                                                 (echos [8] %+ set NEW_YYYY=%XX81%   %+ set NEW_MM=06     %+ set NEW_DD=01     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+                                                                                                 %+ goto :Match_YES)
            if %@LEN[%XX90%] gt 10 .and. %@LEN[%XX91%]==3 .and. %@LEN[%XX92%] == 0 .and.      "%XX10%" == ""                                                                                       (echos [9] %+ set NEW_YYYY=%XX91%5  %+ set NEW_MM=01     %+ set NEW_DD=01     %+ set NEW_HH=12      %+ set NEW_MIN=00     %+                                                                                                 %+ goto :Match_YES)

        :: if we have only examined the filename, but found no matches, then continue on to examine the folder name 
            if "%FOLDERNAME_TRIED%" == "1" goto :Match_NO               %+ REM We will try this once, and once it is tried, we will continue to failure
            set FOLDERNAME_TRIED=1                                      %+ REM Mark that we have tried this
            set CHECKING_IN=%@FULL[%file%]                              %+ REM Refocus our search to the foldername instead of the filename
            echo      ...looking in folder name....                     %+ REM show some kind of indication that we have checked this
            goto :CheckMatches                                          %+ REM and try searching one more time

        :: respond to matches accordingly    
            :Match_NO
                %COLOR_WARNING% %+ echos          `` %+ %COLOR_ALARM% %+ echos No match?! %+ %COLOR_DEBUG% %+ echo  (DATE=%NEW_YYYY%-%NEW_MM%-%NEW_DD%,TIME=%NEW_HH%:%NEW_MIN%) %+ pause
                goto :Match_DONE
            :Match_YES
                %COLOR_SUCCESS% %+ echo       + Match! (DATE=%NEW_YYYY%-%NEW_MM%-%NEW_DD%,TIME=%NEW_HH%:%NEW_MIN%) 
                %COLOR_DEBUG    %+ echos            \--%=>``
                %COLOR_RUN%     %+ if defined NEW_HH .and. defined NEW_MIN goto :Has_Time_YES
                                        :Has_Time_No 
                                            %DEBUGECHO% touch /d%NEW_YYYY%-%NEW_MM%-%NEW_DD%                      %file% %+ goto :Match_DONE
                                        :Has_Time_Yes
                                            %DEBUGECHO% touch /d%NEW_YYYY%-%NEW_MM%-%NEW_DD% /t%NEW_HH%:%NEW_MIN% %file% %+ goto :Match_DONE
            :Match_DONE
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :Usage
        %COLOR_ADVICE% %+ echo USAGE:   %0 *.jpg - fix the dates of all jpgs
        echo EXAMPLE: %0 %%FILEMASK_IMAGE%%;%%FILEMASK_VIDEO%% - fix dates of all images & videos
        pause
    return
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:CleanUp
    :: leave breadcrumb, so we can skip processing once things are fixed
        >%BREADCRUMB%

:END
