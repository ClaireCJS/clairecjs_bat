set TARGET=c:\delme-filelist-names-too-long.txt
call makefilelist
grep -i -E "^.{259,}$"  filelist.txt >%TARGET%
%EDITOR%                              %TARGET%
