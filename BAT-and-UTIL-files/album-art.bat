@echo off

rem Used to automatically look up album art for a search term —— integrated as a "tool" into mp3-tag, which is used as a step in part of our music intake workflow

call image-search-anysize.bat %*
:call image-search-large.bat  %*


