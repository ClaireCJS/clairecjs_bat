@Echo OFF
@on break cancel

:DESCRIPTION: sets DRIVE   to be our current drive letter
:DESCRIPTION: sets DRIVEHD to be our current drive in terms of HDxxx environment variable
:DESCRIPTION: sets LABEL   to be our current drive's volume label

set DRIVE=%cd:~0,1%
set DRIVEHD=%[%DRIVE%]
set LABEL=%@LABEL[%DRIVE%]
