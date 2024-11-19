@on break cancel
@Echo off

set  INPUT=%1
set OUTPUT=%2



if %flac2wav_validated% ne 1  (
    call validate-environment-variables INPUT UTIL
    call validate-in-path               flac.exe
    set flac2wav_validated=1
)
if "%OUTPUT%"=="" (goto :no2)



%UTIL%\flac.exe -d %INPUT% -o %OUTPUT%

goto :END




        :no2
            call error "flac2wav.bat requires %UNDERLINE%2%UNDERLINE_OFF% filenames for input: source flac, target wav"
        goto :END



:END
