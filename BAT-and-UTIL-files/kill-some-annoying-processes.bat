@echo off


rem Check parameters:
        if "%1"=="nops" goto :nops2
                call checktemp
                ps >%temp\tweak-before.txt
        :nops2


rem Show # of processes running before we do our kills:
        %COLOR_WARNING% 
        ps|wc -l 
        %COLOR_NORMAL%

rem Switch to a subtle color before doing our kills
        %COLOR_SUBTLE%

rem added 2023:
        kill /f steamtours*

rem added 2020:
        kill /f icloudservices*
        kill /f musicmanager
        kill /f fahwindow64

rem very sure they can be killed:
        kill /f realsched				>&nul
        kill /f snmp					>&nul
        kill /f konfabulator*			>&nul
        kill /f c2cmonitor				>&nul
        kill /f mitvstreamerclient*		>&nul
        kill /f orb*					>&nul
        kill /f xmltv*					>&nul
        kill /f youtubeuploader         >&nul
        kill /f googleupdate            >&nul

rem mostly sure they can be killed				:
        kill /f NeTmSvNT				>&nul
        kill /f hidserv					>&nul
        kill /f defwatch				>&nul
        kill /f locator					>&nul
        kill /f php*        >&nul
        kill /f httpd       >&nul

rem think it's probably safe to kill:
        kill /f WinMgmt					>&nul
        kill /f MsPMSPSv				>&nul
        kill /f ntvdm*                  >&nul

rem DON'T do this, unless you're prepared to shutdown -a!
        rem DON'T kill /f svchost*
        

rem Allow extra-level kills:
        if /i "%1"=="ultimate" goto :ULTIMATE
                             goto :noULTIMATE
                :ULTIMATE
                        rem verified by article, this must be done in THIS ORDER:
                                kill /f smss            >&nul
                                kill /f winlogon        >&nul
                                kill /f lsass           >&nul
                                kill /f services        >&nul
                        rem moved from supertweak.bat to here:
                                kill /f vncviewer*      >&nul
                                kill /f ntvdm*          >&nul
                                kill /f cavtray         >&nul
                                kill /f cavrid          >&nul
                                kill /f msdtc*          >&nul
                                kill /f ati2evxx*       >&nul
                                kill /f devldr32*       >&nul
                                kill /f xvchost*        >&nul
                                kill /f vetmsg*         >&nul
                                kill /f winmgmt*        >&nul
                                kill /f isafe*          >&nul
                :noULTIMATE

rem Hope it's probably safe to kill:
        :pause
        :kill /f devldr32				>&nul
        :kill /f mstask					>&nul
        :kill /f Dfssvc					>&nul
        :kill /f msdtc					>&nul
        :kill /f svchost*				>&nul

rem unsure of consequences:
        :pause
        :kill /f ntstart				>&nul
        :kill /f regsv*					>&nul
        :kill /f ntvdm*					>&nul
        :kill /f spoolsv				>&nul


rem Safe to kill:
        kill /f REPLIC~1                >&nul
        kill /f googletalkplugin        >&nul
        kill /f ymsgr_tray              >&nul
        kill /f YahooAUService          >&nul
        kill /f PnkBstrA                >&nul
        kill /f GoogleCrashHandler      >&nul
        kill /f BTNtService             >&nul
        kill /f allshare*               >&nul

rem Virus scanner AVG seems to come back after a kill - so kill it to stop a scan:
        kill /f avg*        >&nul

rem kill cryptocurrencies:
        call kill-coins %*      >&nul

:cleanup
        call sleep 1
        if "%1"=="nops" goto :nops
                ps
                ps >%temp\tweak-after.txt
        :nops

:success
        rem Success! Show them the new # of processes running:
        %COLOR_SUCCESS% 
        ps|wc 
        %COLOR_NORMAL%

