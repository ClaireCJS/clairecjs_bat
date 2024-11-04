#!/usr/bin/perl

# On the surface, a general utility like uniq, except it remembers if a line has been seen before —— you don't have to pre-sort it

# Under the hood, this is a post-processor for downloaded lyrics also used to distill lyrics into shorted possible string to use as prompt for OpenAI Whisper transcription, which has a maximum # of tokens of 224, putting an onus to use those 224 tokens efficiently and without repetition. This is also the reason why we change quotes into apostrophes —— because quote are what surrounds the lyrics when used as a commmand-line parameter

# Combine any of these parameters:
#takes a "-L" parameter to treat it as lyrics being fed to an AI for transcription, which need postprocessing from various download sources
#takes a "-A" parameter to print all lines, in case you want to preview the lyric massage while maintaining the normal structure
#takes a "-1" parameter to smush it all into one line



use strict;
use warnings;
my $LYRICS_MODE;
my $ONE_LINE;
my $ALL_LINES_MODE;
my $to_print_last;
my $artist="";
my $title="";
my $album="";

# Loop through @ARGV to check for -1 and -L options
$LYRICS_MODE    = 0;    
$ONE_LINE       = 0;
$ALL_LINES_MODE = 0;
foreach my $arg (@ARGV) {
    if      ($arg eq '-1') {
        $ONE_LINE = 1;
    } elsif ($arg eq '-L') {
        $LYRICS_MODE = 1;
    } elsif ($arg eq '-A') {
        $ALL_LINES_MODE = 1;
    } else {
        die "Unknown argument: $arg\n";
		usage();
		exit 1;
    }
}

my $key;
my $to_print;
my %seen;
my @lines;
if ($LYRICS_MODE) {
	$artist = $ENV{FILE_ARTIST} || "";
	$title  = $ENV{FILE_TITLE } || "";
	$album  = $ENV{ALBUM      } || "";
}
while (<STDIN>) {
	#massage the line
    my $line = $_; 
	$line =~ s/\n//ig;		#get rid of newline

	if ($LYRICS_MODE) {
		#formatting
		$line =~ s/ +$//;					#remove trailing spaces
		$line =~ s/([a-z])$/$1,/ig;			#if line ends in letter, add comma to end of it —— to give WhisperAI a better sense of where to split lines
		$line =~ s/^-+//;					#get rid of lines like: ---------------

		#content
		$line =~ s/\[(Intro|Verse|Pre-Chorus|Refrain|Chorus|Instrumental Break|Solo|[\da-z]+ Solo|Bridge|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]*\]//i;
		$line =~ s/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used//i;
        $line =~ s/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+//i;
        $line =~ s/\*? ?Downloaded from: http:\/\/[^ ]+//i;
		$line =~ s/Get tickets as low as \$[\d\.]+//i;


		#TODO: deal with these:
		#Artist: Circle Jerks, for all artists matching env var of artist which is %FILE_ARTIST%
        #Title: Mrs. Jones,		#http://lyricstranslate.com/en/catch-me-if-you-can-catch-me-if-you-can.html
		#Album tracklist with lyrics
		#        Artist: Circle Jerks,
		#        Album: Vi,
		#        Title: Beat Me Senseless,
		#(chorus) 
		#4TranslationsEspañolРусский
		#([???])
		#
		#
		#



		#commas and quotes
		$line =~ s/^, *$//;
	    $line =~ s/"/'/g;			#for use in AI command line prompt enclosed in quotes

		#dynamic content removals {uses environment variables set in create-lyrics bat}
		if ($artist ne "") { $line =~ s/See $artist Live\b//i; }

		#formatting: dealing with ALL CAPS LYRICS
		#if there are >=10 all-caps letters and no lowercase letters, lowercase the line
		if (($line =~ /[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z]/) && ($line !~ /[a-z]/)) {
			$line = lc($line);
		}


	}


	#key is massaged line  
	$key = lc($line);			 # Convert line to lowercase for case insensitive comparison
	$key =~ s/^ //ig;
	$key =~ s/ $//ig;

	#handle whether we do the new line at the end or not
	$to_print = $line;
	if ($ONE_LINE) { 
		$to_print .=  " "				
	} else { 
		$to_print .= "\n" 
	}

	#print only if unique
    #print $to_print unless $seen{$key}++;

	# store only if unique, postprodess later
	$to_print_last="";
	if (($ALL_LINES_MODE) || (!$seen{$key}++)) {
		if (($LYRICS_MODE==1) && ($to_print_last eq $to_print) && ($to_print !~ /[a-z0-9_-]/)) {
			#Don't print 2 identical blank lines!
		} else {
			push @lines, $to_print;
		}
		$to_print_last = $to_print;
	}

}

# postprocess 
$lines[-1] =~ s/,$// if @lines;				#Remove the comma from the last line if it exists

# Print all lines
# foreach my $line (@lines) { print $line; }
if ($ONE_LINE) {
    # Join all lines into a single string and remove the trailing comma if it exists
    my $final_output = join('', @lines);
    $final_output =~ s/, *$//;  # Remove the trailing comma if it exists
    print $final_output;
} else {
    # Remove the comma from the last line if it exists
    $lines[-1] =~ s/, *$// if @lines;
    # Print all lines
    foreach my $line (@lines) {
        print $line;
    }
}

sub usage {
	print "\n <command> |  unique-lines\n";
	print   " <command> |  unique-lines -1 -- smush into one line\n";
	print   " <command> |  unique-lines -L -- lyrics mode\n";
	print   " <command> |  unique-lines -1 -L -- both (best for AI prompts)\n";
}