@echo off

call validate-environment-variable DROPBOX

%DROPBOX%\

sweep if isdir .git (echo yryr|call deltree .git)