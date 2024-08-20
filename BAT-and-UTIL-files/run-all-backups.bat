@Echo OFF


call validate-in-path important backup-important-files backup-non-repositories backup-repositories backup-stuff


pushd .

call important "This will backup important files, non repositories, then repositories, then 'stuff' (deprecated)"

call backup-important-files
call backup-non-repositories
call backup-repositories
call backup-stuff


popd
