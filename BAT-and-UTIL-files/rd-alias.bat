@Echo On

rem Figure out which argument is the folder
        if isdir %1 set RD_FOLDER=%1
        if isdir %2 set RD_FOLDER=%2
        if isdir %3 set RD_FOLDER=%3
        if isdir %4 set RD_FOLDER=%4
        if isdir %5 set RD_FOLDER=%5
        if isdir %6 set RD_FOLDER=%6
        if isdir %7 set RD_FOLDER=%7
        if isdir %8 set RD_FOLDER=%8
        if isdir %9 set RD_FOLDER=%9
        if isdir %10 set RD_FOLDER=%10
        if isdir %11 set RD_FOLDER=%11
        if isdir %12 set RD_FOLDER=%12
        if isdir %13 set RD_FOLDER=%13
        if isdir %14 set RD_FOLDER=%14
        if isdir %15 set RD_FOLDER=%15
        if isdir %16 set RD_FOLDER=%16
        if isdir %17 set RD_FOLDER=%17
        if isdir %18 set RD_FOLDER=%18
        if isdir %19 set RD_FOLDER=%19
        if isdir %20 set RD_FOLDER=%20

rem Get the FULL path of the folder:
        set RD_FOLDER_FULL=%@FULL[%RD_FOLDER]

rem Remove any FILE_COUNT environment variables (used in cd.bat) related to this folder:
        unset /q file_count_*%RD_FOLDER_FULL%*

rem Actually do the removing :) we add /Nt to not update JPSTREE.IDX for a slight speed increase
        *rd /Nt %*
