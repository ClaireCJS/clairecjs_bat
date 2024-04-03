@Echo off


rem
rem     Passthrough BAT file for aliasing 'copy' to havfe the behavior we want:
rem
rem     1) Piping through our postprocessor to colorize/decorate our copies (if OS >= Windows 10)
rem     2) adding /Nt to not update JPSTREE.IDX because we don't feel that's worth it
rem     3) adding /RCT [new 2024 option] to compress over SMB shares for faster copies
rem



                              set COPYBATPARAMS=%*
if "%OS%" eq "7" (*copy /Nt /RCT /G %COPYBATPARAMS% %+ goto :END)
                  *copy /Nt /RCT /G %COPYBATPARAMS% |& copy-move-post.py 




:END
