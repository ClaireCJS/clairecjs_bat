@echo off
call important "Generating recursive playlist"
call mp3index /s>all.m3u
if exist %filemask_audio% (
    call important "Generating playlist for the files found in the current directory"
    call mp3index >these.m3u
)