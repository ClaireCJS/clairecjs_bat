@Echo on
 on break cancel


rem TODO! This needs to be abstracted using our machinename environment variables

if "%1"==""  goto :usage
if "%1"=="1" goto :MachineeNamIsFirstArgument

goto :usage




:MachineeNamIsFirstArgument
    rem 200708 ——— added start /min exit-after-command - this may royally fuck up the timing in old stuff
    rem 20241125 — added "" after start command to update to windows 10 invocation after deprecating startbat.bat
    

    if "%MAGIC_DOWN"=="1" goto :no_Magic
        if "%MACHINENAME" != "MAGIC"   start "" /min exit-after-command %2 MAGIC   %3 %4 %5 %6 %7 %8 %9
    :no_Magic

    if "%MIST_DOWN"=="1" goto :no_Mist
        if "%MACHINENAME" != "MIST"    start "" /min exit-after-command %2 MIST    %3 %4 %5 %6 %7 %8 %9
    :no_Mist

    if "%HELL_DOWN"=="1" goto :no_Hell
        if "%MACHINENAME" != "HELL"    start "" /min exit-after-command %2 HELL    %3 %4 %5 %6 %7 %8 %9
    :no_Hell

    if "%HADES_DOWN"=="1" goto :no_Hades
        if "%MACHINENAME" != "HADES"   start "" /min exit-after-command %2 HADES   %3 %4 %5 %6 %7 %8 %9
    :no_Hades

    if "%STORM_DOWN"=="1" goto :no_Storm
        if "%MACHINENAME" != "STORM"   start "" /min exit-after-command %2 STORM   %3 %4 %5 %6 %7 %8 %9
    :no_Storm

    if "%FIRE_DOWN"=="1" goto :no_Fire
        if "%MACHINENAME" != "FIRE"    start "" /min exit-after-command %2 FIRE    %3 %4 %5 %6 %7 %8 %9
    :no_Fire

    if "%GOLIATH_DOWN"=="1" goto :no_Goliath
        if "%MACHINENAME" != "GOLIATH" start "" /min exit-after-command %2 GOLIATH %3 %4 %5 %6 %7 %8 %9
    :no_Goliath

    if "%THAILOG_DOWN%"=="1" goto :no_Thailog
        if "%MACHINENAME%" != "THAILOG" start "" /min exit-after-command %2 THAILOG %3 %4 %5 %6 %7 %8 %9
    :no_Thailog

    if "%DEMONA_DOWN%"=="1" goto :no_Demona
        if "%MACHINENAME%" != "DEMONA" start "" /min exit-after-command %2 DEMONA %3 %4 %5 %6 %7 %8 %9
    :no_Demona

    if "%WYVERN_DOWN%"=="1" goto :no_Wyvern
        if "%MACHINENAME%" != "DEMONA" start "" /min exit-after-command %2 DEMONA %3 %4 %5 %6 %7 %8 %9
    :no_Wyvern

goto :end

    :usage
        echo allcomputers 1 a b c d e
        echo ... will do the following command, on each macine: ...
        echo           a <machinename> b c d e
        echo           a <machinename> b c d e
        echo           a <machinename> b c d e
        echo           a <machinename> b c d e
    goto :end

:end
