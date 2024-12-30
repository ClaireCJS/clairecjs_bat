@on break cancel
@echo off
call important "Generating recursive playlist"
call mp3index /s>all.m3u
iff exist %filemask_audio% then
        call important "Generating playlist for the files found in the current directory"
        rem until 2024: call mp3index >these.m3u
        rem 2025:
        call mp3index >these.m3u
endiff
