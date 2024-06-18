@echo off




:::::::::::::::: TODO environm now defines drive letters for everything, so
:::::::::::::::: this can possibly be abstracted out into a version that does
:::::::::::::::: not require maintenance every time there is a hard drive change


REM NAH :PUBLISH:
:DESCRIPTION: displays total free space along with aggregate total at bottom
:REQUIRES: TCMD/4NT/4DOS (for "free" command), PERL (to pipe output to frpost-helper.pl postprocessing script that adds the totals to get the aggregate numbers)
:DEPENDENCIES: frpost.bat, frpost-helper.pl, cat.exe (cygwin)
:REPLACES: OBSOLETE: c:\util\fr5 c (compiled C program I wrote in early 1990s that eventually became un-runnable on modern systems)
:REPLACES: OBSOLETE: celmegs from celerity bbs program (mid-1980s)


    ::::: SETUP:
if not defined TMPTMP (SET TMPTMP="%@UNIQUE[%TEMP]-%*")


::::: SETUP:
    if   "%1" eq "alphabet" goto :By_Alphabet_Parameter
    if   "%1" eq "all"      goto :By_All_Parameter
    if   "%1" eq "abc"      goto :By_Alphabet_Parameter
    if   "%1" eq "ready"    goto :All_Ready_Drives
	if   "%1" != ""         goto :%1            %+ REM       For when we pass usernames, machinemames, or drive letters.
	if   "%1" eq ""         goto :%MACHINENAME% %+ REM       For when we pass   nothing, simply go to current drive letter
    call setDrive       %+  goto :%DRIVE%       %+ REM       For when we pass   nothing, simply go to current drive letter [WHAT USED TO HAPPEN]
    echo * This should never happen.            %+ beep      %+ pause


::::: VALIDATION:
    rem this goes away as we abandon having to maintain this bat file as actively:
    rem call validate-environment-variables HD128G HD240G2 HD2000G5 HD4000G HD4000G2 HD4000G5 HD4000G7 HD6000G1 HD6000G2 HD10T1 HD10T2 HD18T1 HD18T2 HD18T3


:All_Ready_Drives
    free %_DRIVES | frpost >%TMPTMP%
    cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason
    goto :END


:By_Letter_Parameter
    :A
        gosub byLetter A %+ goto :END
    :B
        gosub byLetter B %+ goto :END
    :C
        gosub byLetter C %+ goto :END
    :D
        gosub byLetter D %+ goto :END
    :E
        gosub byLetter E %+ goto :END
    :F
        gosub byLetter F %+ goto :END
    :G
        gosub byLetter G %+ goto :END
    :H
        gosub byLetter H %+ goto :END
    :I
        gosub byLetter I %+ goto :END
    :J
        gosub byLetter J %+ goto :END
    :K
        gosub byLetter K %+ goto :END
    :L
        gosub byLetter L %+ goto :END
    :M
        gosub byLetter M %+ goto :END
    :N
        gosub byLetter N %+ goto :END
    :O
        gosub byLetter O %+ goto :END
    :P
        gosub byLetter P %+ goto :END
    :Q
        gosub byLetter Q %+ goto :END
    :R
        gosub byLetter R %+ goto :END
    :S
        gosub byLetter S %+ goto :END
    :T
        gosub byLetter T %+ goto :END
    :U
        gosub byLetter U %+ goto :END
    :V
        gosub byLetter V %+ goto :END
    :W
        gosub byLetter W %+ goto :END
    :X
        gosub byLetter X %+ goto :END
    :Y
        gosub byLetter Y %+ goto :END
    :Z
        gosub byLetter Z %+ goto :END

    :byLetter [letter]
        if "%@READY[%letter%]" eq "1" goto :Ready_YES
                                      goto :Ready_NO
            :Ready_Yes
                if  "%2" ne "" set  P2=%2:
                if  "%3" ne "" set  P3=%3:
                if  "%4" ne "" set  P4=%4:
                if  "%5" ne "" set  P5=%5:
                if  "%6" ne "" set  P6=%6:
                if  "%7" ne "" set  P7=%7:
                if  "%8" ne "" set  P8=%8:
                if  "%9" ne "" set  P9=%9:
                if "%10" ne "" set P10=%10:
                if "%11" ne "" set P11=%11:
                if "%12" ne "" set P12=%12:
                if "%13" ne "" set P13=%13:
                if "%14" ne "" set P14=%14:
                if "%15" ne "" set P15=%15:
                if "%16" ne "" set P16=%16:
                if "%17" ne "" set P17=%17:
                if "%18" ne "" set P18=%18:
                if "%19" ne "" set P19=%19:
                if "%20" ne "" set P20=%20:
                if "%21" ne "" set P21=%21:
                if "%22" ne "" set P22=%22:
                if "%23" ne "" set P23=%23:
                if "%24" ne "" set P24=%24:
                if "%25" ne "" set P25=%25:
                if "%26" ne "" set P26=%26:
                if "%27" ne "" set P27=%27:
                if "%28" ne "" set P28=%28:
                if "%29" ne "" set P29=%29:

                    free %letter%: %P2% %P3% %P4% %P5% %P6% %P7% %P8% %P9% %P10% %P11% %P12% %P13% %P14% %P15% %P16% %P17% %P18% %P19% %P20% %P21% %P22% %P23% %P24% %P25% %P26% %P27% %P28% %P29% | frpost

                unset /q  P2
                unset /q  P3
                unset /q  P4
                unset /q  P5
                unset /q  P6
                unset /q  P7
                unset /q  P8
                unset /q  P9
                unset /q P10
                unset /q P11
                unset /q P12
                unset /q P13
                unset /q P14
                unset /q P15
                unset /q P16
                unset /q P17
                unset /q P18
                unset /q P19
                unset /q P20
                unset /q P21
                unset /q P22
                unset /q P23
                unset /q P24
                unset /q P25
                unset /q P26
                unset /q P27
                unset /q P28
                unset /q P29
                return
            :Ready_NO
                echo.
                call error "Drive %letter% is not ready. Refusing and resisting."
                return


:By_Username_Parameter
    :claire
    :clio
    :claire
        goto :All_Claire
    :carolyn
        goto :All_Carolyn

:By_Computer_Parameter
    :Mist
        %COLOR_ALARM% %+ echo Mist.... good luck fr'ing Mist!
        goto :end
    :Hell
        %COLOR_ALARM% %+ echo Hell's dead, baby. Hell's dead.
        :free  %HD250G:  | frpost
        goto :end
    :Fire
        free   %SHARE1000G: | frpost
        goto :end
    :Hades
        free %HD256GDERRRRRRRRRRP: | frpost
        goto :end
    :Goliath
        rem free %HD1000G2: %HD2000G5: %HD4000G: %HD4000G2: %HD4000G5: %HD18T2: | frpost
        call fr %DRIVES_GOLIATH% >%TMPTMP%
        cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason
        goto :end
    :Thailog
        rem free %HD240G2: %HD512G:  %HD4000G7: %HD6000G1: %HD6000G2: %HD10T1: %HD10T2: %HD18T1: | frpost
        call fr %DRIVES_THAILOG% >%TMPTMP%
        cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason
        goto :end
    :Demona
        call fr %DRIVES_DEMONA%  >%TMPTMP%
        cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason
        goto :end
    :Wyvern
        call fr %DRIVES_WYVERN%  >%TMPTMP%
        cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason
        goto :end


:By_Alphabet_Parameter
    free A: B: C: D: E: F: G: H: I: J: K: L: M: N: O: P: Q: R: S: T: U: V: W: X: Y: Z: | frpost
    echo.
    call warning "Because every drive letter was used, any C: mapped to another drive letter would be double counted, so this total might be high"
goto :END

:By_All_Parameter
    ::::: 'all' - but depending on who we are we want a diff order because we each care about the drives differently (I care about my own more!)
    :All
        SET TMPTMP="%@UNIQUE[%TEMP]-%*"
        goto :ALL_%USERNAME%
        :All_Claire
            REM free %HD240G2: %HD512G%:  %HD1000G3: %HD2000G5: %HD4000G%: %HD4000G2: %HD4000G5: %HD4000G7: %HD6000G1: %HD6000G2: %HD10T1: %HD10T2: %HD18T1: %HD18T2: %HD18T3: %HD20T1: %HD20T2:| frpost
            call fr %DRIVES_GOLIATH% %DRIVES_WYVERN% %DRIVES_THAILOG% %DRIVES_DEMONA% >%TMPTMP
            cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason

        goto :end
        :All_Carolyn
            REM free %HD240G2: %HD512G%: %HD1000G3:  %HD2000G5: %HD4000G%: %HD4000G2: %HD4000G5: %HD4000G7: %HD6000G1: %HD6000G2: %HD10T1: %HD10T2: %HD18T1: %HD18T2: %HD18T3: %HD20T1: %HD20T2: | frpost
            call fr %DRIVES_THAILOG% %DRIVES_WYVERN% %DRIVES_DEMONA% %DRIVES_GOLIATH% >%TMPTMP
            cat %TMPTMP%                        %+ REM cat_fast isn't reliable in this situation for some reason
        goto :end



:END

