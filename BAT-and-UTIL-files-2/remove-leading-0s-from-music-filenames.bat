@Echo OFF


rem Validate environment:
        if not defined FILEMASK_AUDIO call validate-environment-variable FILEMASK_AUDIO skip_validation_existence
        call validate-in-path rn



rem If 1*.* exists, strip the leading 0’s off:
        rem 2025/04/16: Updating to use RN.bat instead, to automatically rename sidecar files
        rem if not exist 1*.*  for %%audiofile in (%FILEMASK_AUDIO%) if "%@INSTR[0,1,%audiofile%]" eq "0" (     ren "%audiofile%" "%@INSTR[1,,%audiofile%]")
            if not exist 1*.*  for %%audiofile in (%FILEMASK_AUDIO%) if "%@INSTR[0,1,%audiofile%]" eq "0" (call rn  "%audiofile%" "%@INSTR[1,,%audiofile%]" auto)


