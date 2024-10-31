#!/usr/bin/perl
# much like unique, except remembers if a line has been seen before

#takes a "-1" parameter to smush it all into one line
#takes a "-L" parameter to treat it as lyrics being fed to an AI for transcription

# used to distill lyrics into shorted possible string to use as prompt for OpenAI Whisper transcription, which has a maximum # of tokens of 224, putting an onus to use those 224 tokens efficiently and without repetition. This is also the reason why we change " into ' 


use strict;
use warnings;

my $LYRIC_MODE = 1;    
my $ONE_LINE   = 0;
if (($ARGV[0] == "-1") || ($ARGV[1] == "-1") || ($ARGV[2] == "-1")) { $ONE_LINE   = 1; } 
if (($ARGV[0] == "-L") || ($ARGV[1] == "-L") || ($ARGV[2] == "-L")) { $LYRIC_MODE = 1; } 

my $key;
my $to_print;
my %seen;
while (<STDIN>) {
	#massage the line
    my $line = lc($_); # Convert line to lowercase for case insensitive comparison
	$line =~ s/\n//ig;		#get rid of newline

	if ($LYRICS_MODE) {
		$line =~ s/ +$//;					#remove trailing spaces
		$line =~ s/([a-z])$/$1,/ig;			#if line ends in letter, add comma to end of it —— to give WhisperAI a better sense of where to split lines
	}


	#key is massaged line
	$key = $line;
	$key =~ s/^ //ig;
	$key =~ s/ $//ig;

	#to-print stuff only
	$to_print = $line;
	if ($ONE_LINE) { 
		$to_print =~ s/"/'/g;
		$to_print .=  " " 
	}
	else           { $to_print .= "\n" }

	#print only if unique
    print $to_print unless $seen{$key}++;
}
