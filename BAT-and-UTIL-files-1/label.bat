@on break cancel
@Echo OFF

label.exe %*

call setdrive
call make-directory-matching-drive-label.bat %drive%


