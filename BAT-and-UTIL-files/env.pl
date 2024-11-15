#!c:\perl\perl\bin\perl
###!/usr/bin/perl

#Prints out the environment much like the unix `env` command
foreach $key (sort keys %ENV) { print "\%$key=$ENV{$key}\n"; }
