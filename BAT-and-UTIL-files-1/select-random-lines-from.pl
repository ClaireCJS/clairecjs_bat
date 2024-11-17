#!/usr/bin/perl
use strict;


##### PROCESS ARGUMENTS:
my $NUM_LINES_TO_GET = $ARGV[0]; die("1st argument must be positive number" ) if (($NUM_LINES_TO_GET !~ /^\d+$/) || ($NUM_LINES_TO_GET < 0));
my $INPUT_FILE       = $ARGV[1]; die("2nd argument must be file that exists") if (not -e $INPUT_FILE);

##### READ IN FILE:
open      (INPUT_FILE,$INPUT_FILE) || die("could not open input file $INPUT_FILE");
my @LINES=<INPUT_FILE>;
close     (INPUT_FILE);

##### SELECT RANDOM LINES:
use List::Util qw/shuffle/;
my @shuffled_indexes = &shuffle(0..@LINES);								#Shuffled list of indexes into @deck
my @pick_indexes     = @shuffled_indexes[0 .. $NUM_LINES_TO_GET - 1];	#Get just N of them.
my @picks            = @LINES[@pick_indexes];							#Pick cards from @deck

##### PRINT THE RANDOM LINES:
print @picks;

