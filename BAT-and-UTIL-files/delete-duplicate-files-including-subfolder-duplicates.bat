@Echo off

REM /SHA1 is slightly faster but potentially insecure
REM /Nj  isn't working right dammit

               set FILES=*.*
if "%1" ne "" (set FILES=%1)

%color_warning_less%
dedupe %FILES% /A: /D /P /R /S /V /SHA1  .
%color_normal%

REM     
REM    Options:
REM        /= Display the DEDUPE command dialog to help you set the filename and command line options. The /= option can be anywhere on the line; additional options will set the appropriate fields in the command dialog. 
REM        /A: Dedupe those files that have the specified attribute(s) set. See Attribute Switches for information on the attributes which can follow /A:. Do not use /A: with @file lists. See @file lists for details. 
REM        You can specify /A:= to display a dialog to help you set individual attributes.
REM        /D Delete duplicate files 
REM        /H Convert duplicate files to hard links to the first file. 
REM        /L Convert duplicate files to symlinks of the first file. Note that to create symlinks, you must be in an elevated session. 
REM        /N Change default options. This can be any combination of the following: 
REM                    d Skip hidden directories (when used with /S) 
REM                    e Don't display errors 
REM                    f Don't display the bytes freed in the summary 
REM                    j Skip junctions (when used with /S) 
REM                    s Don't display the summary 
REM                    t Don't update the CD / CDD extended directory search database (JPSTREE.IDX) 
REM                    z Skip system directories (when used with /S) 
REM        /P Prompt before deleting or symlink'ing files. 
REM        /Q Quiet (don't display directories or files as they are processed) 
REM        /R Delete to the recycle bin 
REM        /Sn Search subdirectories 
REM        /SHAx Hash algorithm to use. The default is SHA256; you can optionally use SHA1 or SHA512. SHA1 is slightly faster but potentially insecure. 
REM        /V Verbose output 
REM        /Wn Wipe deleted files 
REM     
REM      
