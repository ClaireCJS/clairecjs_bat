#!/usr/bin/perl

# much like unique, except remembers if a line has been seen before, and takes a "-1" parameter to smush it all into one line

# used to distill lyrics into shorted possible string to use as prompt for OpenAI Whisper transcription, which has a maximum # of tokens of 224, putting an onus to use those 224 tokens efficiently and without repetition

use strict;
use warnings;

my $ONE_LINE=0;
if ($ARGV[0] == "-1") { $ONE_LINE=1; } 

my $key;
my $to_print;
my %seen;
while (<STDIN>) {
    my $line = lc($_); # Convert line to lowercase for case insensitive comparison
	$line =~ s/\n//ig;

	$key = $line;
	$key =~ s/^ //ig;
	$key =~ s/ $//ig;

	$to_print = $line;
	if ($ONE_LINE) { $to_print .=  " " }
	else           { $to_print .= "\n" }
    print $to_print unless $seen{$key}++;
}
