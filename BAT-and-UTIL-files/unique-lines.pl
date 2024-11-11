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
        die "\n\n\nUnknown argument: $arg\n\n\nUSAGE:\n\t-1 for smushing into 1 line\n\t-A to show ALL lines not just unique lines\n\t-L for downloaded-lyric postprocessing";
		usage();
		exit 1;
    }
}

my $key;
my $to_print;
my %seen;
my @lines;
my $test;
my $test1;
my $test2;
my $file_artist="";
my $file_title="";
my $file_album="";
my $original_line;
my $file_orig_artist;
my $i="";
                  
if ($LYRICS_MODE) {
	$file_artist      = $ENV{FILE_ARTIST}      || "";
	$file_orig_artist = $ENV{FILE_ORIG_ARTIST} || "";
	$file_title       = $ENV{FILE_TITLE }      || "";
	$file_album       = $ENV{ALBUM      }      || "";
}
my $line_number=0;
while (<STDIN>) {
	#massage the line
    my $line = $_; 
	$line =~ s/\n//ig;		#get rid of newline
	$line_number++;
	my $original_line=$line;

	if ($LYRICS_MODE) {
		#pre-processing
		$line =~ s/ +$//;					#remove trailing spaces
		$line =~ s/([a-z])$/$1,/ig;			#if line ends in letter, add comma to end of it —— to give WhisperAI a better sense of where to split lines


		#first-line-only stuff to red rid of
		if ($line_number == 1) {
			#line =~ s/(\d)([^\d]+)/$2/;		#remove  only 1 leading digit  from 1ˢᵗ line if it's just a single digit 'cause I've noticed that happens a lot
			$line =~ s/(\d{1-2})([^\d]+)/$2/;	#remove up to 2 leading digits from 1ˢᵗ line if it's just a single digit 'cause I've noticed that happens a lot
		}

		#divider lines to get rid of
		$line =~ s/^-+//;					#get rid of lines like: ---------------

		#song sections to get rid of
		for ($i=1; $i<=2; $i++) {			#twice to get things like "Intro/Chorus" or "Guitar Solo/Bridge", which meant changing the regex to include an ending of / where previously it just included ]
			#line =~   s/[\[\(]?(Intro|Sample|Hook|Verse|Pre\-Chorus|Refrain|Chorus|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Bridge|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]*[\]\)\/]?//i;
			$line =~ s/[\[\(]? ?(Sample|Intro|Hook|Build:? ?[a-z &]+|Verse|Pre\-Chorus|Refrain|Drop|Chorus|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Bridge|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;
		}


		#website crap to get rid of
		$line =~ s/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used//i;
        $line =~ s/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+//i;
        $line =~ s/\*? ?Downloaded from: http:\/\/[^ ]+//i;
		$line =~ s/Album tracklist with lyrics//;

		#advertising crap to get rid of
		$line =~ s/Get tickets as low as \$[\d\.]+//i;

		#dynamic content removals {uses environment variables set in create-lyrics bat}		
		if ($file_artist ne "") { 
			$line =~ s/See \Q$file_artist Live\E//i; 
			$line =~ s/Artist: \Q$file_artist\E,?//i; 
		}
		if ($file_title ne "") { 
			$line =~ s/Title: \Q$file_title\E,?//i; 
		}
		if ($file_album ne "") { 
			$line =~ s/Album: \Q$file_album\E,?//i; 
		}

		#commas and quotes
		$line =~ s/^, *$//;			#remove leading comma like ", a line of text"
	    $line =~ s/"/'/g;			#change quotes to apostrophes so these can be used as a quoted command line argument

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
		$to_print .=  " ";
	} else { 
		$to_print .= "\n";
	}

	#print only if unique
    #print $to_print unless $seen{$key}++;

	# store only if unique, postprodess later
	$to_print_last="";
	if ($LYRICS_MODE==1) { $test=(($ALL_LINES_MODE) || (!$seen{$key}++) || ($original_line eq "")); }
	else                 { $test=(($ALL_LINES_MODE) || (!$seen{$key}++)); }
	if ($test) {
		if (($LYRICS_MODE==1) && ($to_print_last eq $to_print) && ($to_print !~ /[a-z0-9_-]/)) {
			#Don't print 2 identical non-lyric lines!?
		} else {
			push @lines, $to_print;
		}
		$to_print_last = $to_print;
	}

}

# postprocessing for when lines are separate:
$lines[-1] =~ s/,$// if @lines;				#Remove the comma from the last line if it exists

my $output="";

# Print all lines
# foreach my $line (@lines) { print $line; }
if ($ONE_LINE) {
    # Join all lines into a single string and remove the trailing comma if it exists
    my $final_output = join('', @lines);
    $final_output =~ s/, +$//;  # Remove the last trailing comma if it exists
    print $final_output;
} else {
	# postprocessing for when lines are together:
    # Remove the comma from the last line if it exists
    $lines[-1] =~ s/, *$// if @lines;
    # Print all lines
    foreach my $line (@lines) {
        $output .= $line;
    }
	#$output =~ s/\n\n\n/\n\n/g;
}
print $output;

sub usage {
	print "\n <command> |  unique-lines\n";
	print   " <command> |  unique-lines -1 -- smush into one line\n";
	print   " <command> |  unique-lines -L -- lyrics mode\n";
	print   " <command> |  unique-lines -1 -L -- both (best for AI prompts)\n";
}