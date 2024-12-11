@Echo OFF

call validate-environment-variable FILEMASK_AUDIO

:originally used if not exist 1%FILEMASK_AUDIO% but it actually only worked for the first (mp3) extension listed in %FILEMASK_AUDIO%

if not exist 1*.*  for %%audiofile in (%FILEMASK_AUDIO%) if "%@INSTR[0,1,%audiofile%]" eq "0" (ren "%audiofile%" "%@INSTR[1,,%audiofile%]")

