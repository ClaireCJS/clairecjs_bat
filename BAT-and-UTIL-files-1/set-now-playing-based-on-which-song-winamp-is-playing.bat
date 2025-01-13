@loadbtm on
@Echo off
set    NOW_PLAYING=%@EXECSTR[get-current-song-playing.pl]
%COLOR_DEBUG
echo * NOW_PLAYING set to %NOW_PLAYING%
%COLOR_NORMAL

