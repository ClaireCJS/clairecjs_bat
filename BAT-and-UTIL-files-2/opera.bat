@echo off
@on break cancel
pushd .

if "%1"=="old" goto :old

    :new

        :Opera_64bit_Demona
            %localappdata%
            cd Programs
            cd Opera
            if exist opera.exe goto :StartOpera

        :Opera_64bit
            REM *********** put new 64-bit opera versions *on top* so they happen first *********** 
            call pf.bat
            if exist Opera cd Opera
            if isdir 50.0.2762.67 cd 50.0.2762.67
            if exist opera.exe goto :StartOpera

        :Opera_32bit
            REM *********** put new 32-bit opera versions *on top* so they happen first *********** 
            call pf2.bat
            cd "Opera"
            opera.exe
            :gosub checkversion 52.0.2871.64
            :gosub checkversion 51.0.2830.55   
            :gosub checkversion 50.0.2762.67   
            :osub checkversion 42.0.2393.94_0 
            :osub checkversion 41.0.2353.56_0  %+ REM this is a downgrade!
            :osub checkversion 42.0.2393.85_0 
            :osub checkversion 41.0.2353.56   
            :osub checkversion 40.0.2308.90   
            :osub checkversion 40.0.2308.62   
            :osub checkversion 39.0.2256.48   
            :osub checkversion 38.0.2220.31   
            :osub checkversion 37.0.2178.54   
            :osub checkversion 37.0.2178.32   
            :osub checkversion 36.0.2130.66   
            :osub checkversion 36.0.2130.46   
            REM ****************************************************************************


        :OperaNotFound
           if not exist opera.exe (%COLOR_ALARM% %+ echo where is opera.exe? did it upgrade or something? %+ pause %+ dir %+ goto :The_Very_End)
        goto :END

        :CheckVersion [ver]            
            if isdir %ver% goto :is
                           goto :isnt
                :is
                    %COLOR_IMPORTANT% 
                    echo * Found Opera version %ver%! 
                    %COLOR_NORMAL%
                    cd %ver%
                    goto :StartOpera
                :isnt
            return

        :StartOpera
            start Opera.exe --disable-update
    goto :end

    :old
        call pf1.bat
        call pf2.bat
        cd "Opera"
        start Opera.exe
    goto :end



:END
    cd \
    popd
:The_Very_End