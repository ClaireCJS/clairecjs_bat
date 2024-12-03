@echo off
 on break cancel

:PUBLISH:
:DESCRIPTION: prefix any command line with wrapper to make it autowrap long filenames into short filenames, for backwards compatibility with old DOS programs such as your favorite text editors
:REQUIRES: 4DOS/4NT/TCMD (for %@SFN[<longfilename>] short filename function)



::::: Change arguments into short filenames:

    REM   This is ugly, okay?  
    REM   It was written in the 1990s and works and I just don't feel like fixing it.

    GoSub ChangeToShort ARGV2   %1
    GoSub ChangeToShort ARGV2   %2
    GoSub ChangeToShort ARGV3   %3
    GoSub ChangeToShort ARGV4   %4
    GoSub ChangeToShort ARGV5   %5
    GoSub ChangeToShort ARGV6   %6
    GoSub ChangeToShort ARGV7   %7
    GoSub ChangeToShort ARGV8   %8
    GoSub ChangeToShort ARGV9   %9
    GoSub ChangeToShort ARGV10 %10
    GoSub ChangeToShort ARGV11 %11
    GoSub ChangeToShort ARGV12 %12
    GoSub ChangeToShort ARGV13 %13
    GoSub ChangeToShort ARGV14 %14
    GoSub ChangeToShort ARGV15 %15
    GoSub ChangeToShort ARGV16 %16
    GoSub ChangeToShort ARGV17 %17
    GoSub ChangeToShort ARGV18 %18
    GoSub ChangeToShort ARGV19 %19
    GoSub ChangeToShort ARGV20 %20
    rem ^^^^^^^^^^^^^^^^^^^^^^^^^^ ———— should use a loop and SHIFT to gracefully process an infinite # of parameters, 
    rem                                 ...but pasting this was faster and this has never happened in decades




rem Make correct window title, special case if its our text editor:
        iff "%1"=="%EDITOR" then
            GoSub TitleAlt
        elseiff %@INDEX[%1,e50] ge 0 then
            GoSub TitleAlt
        elseiff %@INDEX[%1,e.exe] ge 0 then
            GoSub TitleAlt
        else
            call print-if-debug "Using standard titling scheme..."
            call fix-window-title
        endiff
        :pause


rem Run the new modified command line:
        call print-if-debug "* cmdline is %*"
        %1 %ARGV2 %ARGV3 %ARGV4 %ARGV5 %ARGV6 %ARGV7 %ARGV8 %ARGV9
        goto :END


            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            :ChangeToShort [varname tmpArg]
                if "%@UNQUOTE[%tmparg]" eq "" goto :Nope
                    call print-if-debug "varname is %varname ... tmparg is %tmpArg .. SFN[%tmpArg]=%@SFN[%tmpArg]"
                    if %@len[%tmpArg] eq 2 goto :Nevermind_Its_Just_Empty_Quotes
                    iff exist %tmpArg .or. exist "%tmpArg%" .and. "%@INDEX[%tmpArg,*]"=="-1" .and. "%@INDEX[%tmpArg,?]"=="-1" .and. ("%OS%" ne "7" .and."%OS%" ne "ME" .and. "%OS%" ne "98" .and. "%OS%" ne "95") then
                        set %varname="%@UNQUOTE[%@SFN[%tmpArg]]"
                        call print-if-debug "%wide%shortening %tmparg"
                    else
                        set %varname=%tmpArg
                        call print-if-debug "%wide%not shortening %tmparg"
                    endiff
                    :Nevermind_Its_Just_Empty_Quotes
                    call print-if-debug "varname is now '%varname%'"
                :Nope
            return
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            :TitleAlt
                rem call debug "Using alternate titling scheme..."
                title %2 %3 %4 %5 %6 %7 %8 %9
            return
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
