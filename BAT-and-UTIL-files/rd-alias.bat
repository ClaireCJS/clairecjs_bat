@Echo On

rem Figure out which argument is the folder:
        repeat 20 if isdir %[%_repeat] set RD_FOLDER=%[%_repeat]

rem Get the FULL path of that folder:
        set RD_FOLDER_FULL=%@FULL[%RD_FOLDER]

rem Remove any FILE_COUNT environment variables (used in cd.bat) related to this folder:
        unset /q file_count_*%RD_FOLDER_FULL%*

rem Actually do the removing :) we add /Nt to skip updating JPSTREE.IDX file in order to achive a neglible speed increase
        *rd /Nt %*
