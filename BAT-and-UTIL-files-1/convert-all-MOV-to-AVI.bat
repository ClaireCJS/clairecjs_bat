@echo off
echo * Think about your fixed_quant setting:
echo ...... 1-3=very little degredation/huge files
echo ...... 4-5=good for high qual vid
echo ......  31=lowest
echo quant=4  made a 47M file to a 41.6M file, but still too big for flickr API -- however, can barely see any degredation at 4
echo quant=5  made a 47M file to a 33.1M file
echo quant=6  made a 47M file to a 27.0M file
echo quant=7  made a 47M file to a 23.2M file
echo quant=8  made a 47M file to a 19.7M file
echo quant=9  made a 47M file to a 17.4M file
echo quant=10 made a 47M file to a 15.3M file
echo quant=11 made a 47M file to a 13.9M file -- still some visible ugliness, but my 1.5min video had to go this far to get command-line API uploaded (sigh)
echo quant=15 made a 47M file to a  9.8M file
echo quant=20 made a 47M file to a  7.3M file -- but wayyyy too low quality!

set fixed_quant=4
eset fixed_quant






if "%fixed_quant"=="" goto :no_env_quant

:yes_env_quant
for %%1 in (*.mov) call mov2avi.bat "%%1" "%@NAME[%%1] (xvid) (quant=%fixed_quant%).avi"
goto :cleanup

:no_env_quant
for %%1 in (*.mov) call mov2avi.bat "%%1" "%@NAME[%%1] (xvid).avi"
goto :cleanup


:cleanup
:call deprecate *.mov
:END
