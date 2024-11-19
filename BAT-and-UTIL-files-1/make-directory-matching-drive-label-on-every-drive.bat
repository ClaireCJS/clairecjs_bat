@on break cancel
@echo off
set  sure=0
call warning "Are you really sure? If so, change SURE to 1!"
eset sure

call do-command-on-all-drives make-directory-matching-drive-label

unset /q sure