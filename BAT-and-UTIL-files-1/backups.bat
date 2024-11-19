@Echo OFF
 on break cancel

call set-ansi force

call warning "This is JUST backing up important files, then repositories "
call warning "To run full backup set with dropbox sync and deprecated backup scripts, run '%italics_on%run-all-backups%italics_off%'"

call backup-important-files   %*
call backup-important-folders %*
call backup-repositories      %*


