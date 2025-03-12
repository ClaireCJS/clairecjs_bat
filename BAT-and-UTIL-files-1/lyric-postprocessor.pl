#TODO: possibly shorten things like ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo
#!/usr/bin/perl

# Lyric postprocessor for AI transcription prompts!
#
#		
# Combine any of these command-line parameters:
#     [DEFAULT] “-U” parameter to print unique lines only
#               “-A” parameter to print *all*  lines
#               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#     [DEFAULT] “-L” parameter to treat it as downloaded lyrics, which need extended/special postprocessing 
#               “-N” parameter to treat it as downloaded lyrics, which need extended/special postprocessing 
#               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               “-1” parameter to     smush it all into one line {for AI command-line prompting}
#     [DEFAULT] “-0” parameter to NOT smush it all into one line 
#               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#     [DEFAULT] “-P” parameter to     add character to end of each line
#               “-S” parameter to NOT add character to end of each line


#HISTORY: forked from “lyric-postprocessor.pl”

########### CONFIGURATION: BEGIN: ###########
my $ADDED_END_LINE_CHARACTER=".";					#character to append to each line of lyrics, since people don't typically add periods or commas to the end of posted lyrics online
########### CONFIGURATION: ^^^END ###########


use strict;
use warnings;
my $LYRICS_MODE;
my $ONE_LINE;
my $UNIQUE_LINES_MODE;
my $ADD_CHARACTER_MODE;
   
# Default modes:
$LYRICS_MODE        = 1;
$ONE_LINE           = 0;
$UNIQUE_LINES_MODE  = 0;
$ADD_CHARACTER_MODE = 1;

# Loop through @ARGV to check for -1 and -L options
foreach my $arg (@ARGV) {

    if      ($arg eq '-1') {				#smush into 1 line or not
        $ONE_LINE = 1;
    } elsif ($arg eq '-0') {
        $ONE_LINE = 0;

    } elsif ($arg eq '-L') {				#lyric mode or not
        $LYRICS_MODE = 1;
    } elsif ($arg eq '-N') {
        $LYRICS_MODE = 0;

    } elsif ($arg eq '-A') {				#all lines or only unique lines
        $UNIQUE_LINES_MODE = 0;
    } elsif ($arg eq '-U') {
        $UNIQUE_LINES_MODE = 1;

    } elsif ($arg eq '-P') {				#add a char (periods for my 1ˢᵗ use) to the end of every line
        $ADD_CHARACTER_MODE = 1;
    } elsif ($arg eq '-S') {
        $ADD_CHARACTER_MODE = 0;

	} elsif ($arg eq '-H') {
		show_usage();
		exit 1;

    } else {
        #die "\n\n\nUnknown argument: $arg\n\n\nUSAGE:\n\t-1 for smushing into 1 line\n\t-A to show ALL lines not just unique lines\n\t-L for downloaded-lyric postprocessing";
		show_usage();
		exit 1;
    }
}

my $key;
my $to_print="";
my $to_print_last="";
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
my $do_it=-1;
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

		#first-line-only stuff to red rid of
		if ($line_number == 1) {
			#line =~ s/(\d)([^\d]+)/$2/;		#remove  only 1 leading digit  from 1ˢᵗ line if it's just a single digit 'cause I've noticed that happens a lot
			$line =~ s/(\d{1-3})([^\d]+)/$2/;	#remove up to 3 leading digits from 1ˢᵗ line [2 weren't enough!]
		}

		#divider lines to get rid of
		$line =~ s/^-+//;					#get rid of lines like: ---------------

		#song sections to get rid of
		for ($i=1; $i<=2; $i++) {			#twice to get things like "Intro/Chorus" or "Guitar Solo/Bridge", which meant changing the regex to include an ending of / where previously it just included ]
			#line =~    s/[\[\(]?(Intro|Sample|Hook|Verse|Pre\-Chorus|Refrain|Chorus|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Bridge|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]*[\]\)\/]?//i;
			$line =~    s/[\[\(]? ?(Sample|Sample \d+|Intro|Intro \d+|Hook|Build:? ?[a-z &]+|Verse|Verse +\d|Pre\-Chorus|Refrain|Refrain +\d|Drop|Chorus|Chorus \d|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Solo +\d+|Bridge|Instrumental Interlude|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;
			$line =~ s/\d?[\[\(]? ?(Sample|Sample \d+|Intro|Intro \d+|Hook|Build:? ?[a-z &]+|Verse|Verse +\d|Pre\-Chorus|Refrain|Refrain +\d|Drop|Chorus|Chorus \d|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Solo +\d+|Bridge|Instrumental Interlude|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;
		}


		#website crap to get rid of
		$line =~ s/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used//i;
        $line =~ s/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+//i;
        $line =~ s/\*? ?Downloaded from: http:\/\/[^ ]+//i;
		$line =~ s/Album tracklist with lyrics//;

		#the word “Embed” is sometimes tacked onto the end of a line of downloaded lyrics:
		$line =~ s/You might also like//i;
		$line =~ s/^(.*[a-zA-Z])Embed\.?$/$1/i;

		#advertising crap to get rid of
		$line =~ s/Get tickets as low as \$[\d\.]+//i;

		#dynamic content removals {uses environment variables set in create-lyrics bat}		
		if ($file_artist ne "") { 
			$line =~ s/See \Q$file_artist Live\E//i; 
			$line =~ s/Artist: \Q$file_artist\E[\.,]?//i; 
		}
		if ($file_title ne "") { 
			$line =~ s/Title: \Q$file_title\E[\.,]?//i; 
		}
		if ($file_album ne "") { 
			$line =~ s/Album: \Q$file_album\E[\.,]?//i; 
		}

		#commas and quotes
		$line =~ s/^, *$//;			#remove leading comma like ", a line of text"
	    $line =~ s/"/'/g;			#change quotes to apostrophes so these can be used as a quoted command line argument

		#formatting: dealing with ALL CAPS LYRICS
		#if there are >=10 all-caps letters and no lowercase letters, lowercase the line
		if (($line =~ /[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z]/) && ($line !~ /[a-z]/)) {
			$line = lc($line);
		}

		#fix crap like: “ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo”
		# Use regex to match any character repeated more than 24 times and replace it with 24 of that character
		$line =~ s/(\w)\1{24,}/$1 x 24/eg;


		#however our environment variables aren’t always set, 
		#so we ended up needing to do this more aggressively:
		$line =~  s/^Album: [\w\s]+\.?$//i; 
		$line =~  s/^Title: [\w\s]+\.?$//i; 
		$line =~ s/^Artist: [\w\s]+\.?$//i; 
		$line =~     s/^id: [\w\s]+\.?$//i; 

		$line =~ s/^ *//g;
		$line =~ s/ *$//g;

		#add our invisible character at the end but do it Last!
		if (($ADD_CHARACTER_MODE) && ($line ne "")) {
			$line =~ s/([a-z0-9])$/$1$ADDED_END_LINE_CHARACTER/ig;			#if line ends in letter, add comma to end of it —— to give WhisperAI a better sense of where to split lines
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
		#print "to_print is “$to_print”\n";
		if (($to_print eq "") && ($to_print_last eq "")) {
			$do_it = 0;
		} else {
			$do_it = 1;
			$to_print .= "\n";
		}
	}

	#print only if unique
    #print $to_print unless $seen{$key}++;

	# store only if unique, postprocess later
	#why? $to_print_last="";
	if ($LYRICS_MODE==1) { $test=((!$UNIQUE_LINES_MODE) || (!$seen{$key}++) || ($original_line eq "")); }
	else                 { $test=((!$UNIQUE_LINES_MODE) || (!$seen{$key}++)); }
	if ($test) {
		if (($LYRICS_MODE==1) && ($to_print_last eq $to_print) && ($to_print !~ /[a-z0-9_-]/) && ($to_print ne "") && ($to_print ne "\n")) {
			#Don't print 2 identical non-lyric lines!?
			if (!$UNIQUE_LINES_MODE) { push @lines, $to_print; }
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

	#very final postprocessing:
    $final_output =~ s/, +$//;		# Remove the last trailing “,” [comma] if it exists
    $final_output =~ s/^\d\.? ?//;  # Remove “1. ”-type stuff at beginning
	#$final_output =~ s/
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

sub show_usage {
	print "\n <command> |  lyric-postprocessor\n";
	print   " <command> |  lyric-postprocessor -A -- print only unique lines: OFF [default]\n";
	print   " <command> |  lyric-postprocessor -U -- print only unique lines: ON\n";
	print   " <command> |  lyric-postprocessor -N -- lyric postprocessing mode OFF [default]\n";
	print   " <command> |  lyric-postprocessor -L -- lyric postprocessing mode ON\n";
	print   " <command> |  lyric-postprocessor -0 -- smush into one line: OFF [default]\n";
	print   " <command> |  lyric-postprocessor -1 -- smush into one line: ON\n";
	print   " <command> |  lyric-postprocessor -P -- add “$ADDED_END_LINE_CHARACTER” character to end of line: ON [default]\n";
	print   " <command> |  lyric-postprocessor -S -- add “$ADDED_END_LINE_CHARACTER” character to end of line: OFF\n";
	print   "\nNOTE: Changes \" into \’ as well in most/all circumstances";	
}
# Combine any of these command-line parameters:
#               “-U” parameter to print unique lines only
#     [DEFAULT] “-A” parameter to print *all*  lines
#               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#     [DEFAULT] “-L” parameter to treat it as downloaded lyrics, which need extended/special postprocessing 
#               “-N” parameter to treat it as downloaded lyrics, which need extended/special postprocessing 
#               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               “-1” parameter to     smush it all into one line {for AI command-line prompting}
#     [DEFAULT] “-0” parameter to NOT smush it all into one line 
#               ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#     [DEFAULT] “-P” parameter to     add character to end of each line
#               “-S” parameter to NOT add character to end of each line

