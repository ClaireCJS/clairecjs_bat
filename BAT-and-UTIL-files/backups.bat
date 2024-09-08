@Echo OFF

call warning "This is JUST backing up repositories & important files"
call warning "To run full backup set with dropbox sync and deprecated backup scripts, run '%italics_on%run-all-backups%italics_off%'"

call backup-important-files   %*
call backup-important-folders %*
call backup-repositories      %*


