while 1=1
{
Sleep, 4
Loop, %USERPROFILE%\AppData\Roaming\Winamp\Plugins\milk_msg.ini
{
    copy_it = n
    IfNotExist, %USERPROFILE%\AppData\Roaming\Winamp\Plugins\milk2_msg.ini  ; Always copy if target file doesn't yet exist.
        copy_it = y
    else
    {
        FileGetTime, time, %USERPROFILE%\AppData\Roaming\Winamp\Plugins\milk2_msg.ini
        EnvSub, time, %A_LoopFileTimeModified%, seconds  ; Subtract the source file's time from the destination's.
        if time < 0  ; Source file is newer than destination file.
            copy_it = y
    }
    if copy_it = y
    {
        FileCopy, %USERPROFILE%\AppData\Roaming\Winamp\Plugins\milk_msg.ini, %USERPROFILE%\AppData\Roaming\Winamp\Plugins\milk2_msg.ini, 1   ; Copy with overwrite=yes
        ControlSend, , {f7}00, MilkDrop 2
    }
     
}
}