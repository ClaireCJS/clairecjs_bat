#!/usr/local/bin/perl

my @LINES=<STDIN>;
for ($i=0; $i<(@LINES); $i++) {
  chomp $LINES[$i];
  print $LINES[$i];
  if ($i<@LINES-1) { print " "; }
}

