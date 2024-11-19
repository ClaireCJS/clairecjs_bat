@Echo off
@on break cancel

call removal "Killing explorer to run move command without explorer's interference"
        kill /f explorer
        call sleep 1


call less_important "Performing the file move..."
mv %*


call less_important "Restarting explorer"
        explorer
