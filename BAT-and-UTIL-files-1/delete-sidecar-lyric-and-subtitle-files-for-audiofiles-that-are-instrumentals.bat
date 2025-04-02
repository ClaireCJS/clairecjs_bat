@Echo OFF


set INSTRUMENTAL_PROCESSING_MODE=1
call delete-sidecar-lyric-and-subtitle-files-for-audiofiles-in-lyricless-approved-state.bat %*
set INSTRUMENTAL_PROCESSING_MODE=0


