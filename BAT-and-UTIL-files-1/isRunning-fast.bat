@on break cancel
@echo off

REM this is like isRunning except instead of using a regular expression for a relaxed call
REM this uses the internal TCC process functoin which only works with:

REM     an exact .exe name


set  isRunning_fast=1
call isRunning %*
set  isRunning_fast=0

