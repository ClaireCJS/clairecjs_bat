#!/usr/bin/perl

################################################################################
#                      Lyric Postprocessor for AI/etc                          #
#                      Lyric Postprocessor for AI/etc                          #
#                      Lyric Postprocessor for AI/etc                          #
#                                                                              #
# Description:                                                                 #
# This script cleans up and processes raw lyrics (or similar line-based text)  #
# for use in AI transcription or prompt systems like WhisperAI. It removes     #
# common junk, standardizes formatting, optionally compresses output into a    #
# single line, and inserts punctuation to help AI models split phrases better. #
#                                                                              #
# Supports input via STDIN (piping) or via filename passed as a parameter.     #
#                                                                              #
# Usage Examples:                                                              #
#     cat lyrics.txt |  perl lyric-postprocessor.pl -1 -U -L                   #
#     perl lyric-postprocessor.pl -1 -U -L lyrics.txt                          #
#     perl lyric-postprocessor.pl lyrics.txt -1 -U -L                          #
#                                                                              #
# Flags:                                                                       #
#     -U   Unique lines only                                                   #
#     -A   All lines (default)                                                 #
#     -L   Enable lyric-specific cleaning (default)                            #
#     -N   Disable lyric-specific cleaning                                     #
#     -1   Smush output into a single line                                     #
#     -0   Output separate lines (default)                                     #
#     -P   Add '.' to end of lyric lines (default)                             #
#     -S   Do not add end-of-line punctuation                                  #
#     -H   Show help/usage                                                     #
#                                                                              #
# Environment Variables (optional):                                            #
#     FILE_ARTIST, FILE_TITLE, FILE_ALBUM, FILE_ORIG_ARTIST                    #
#     Used to remove dynamic artist/title/album mentions in downloaded text    #
#                                                                              #
# Key Features:                                                                #
#   - Converts ALL-CAPS lyrics to not be all caps							   #
#   - Removes junk: advertising lines, metadata, section titles, dividers      #
#   - Fixes excessive repetition (e.g., ooooooo → oooooooooooooooooooooooo)    #
#   - Adds “.” to the end of each line by default, for better WhisperAI        #
#                                    parsing with the --sentence option        #
#   - Changes ' into ’                                                         #
#   - Removes lyric website advertising spam 								   #
#   - Removes song-section titles like “[chorus]” or “[spoken]”				   #
#   - Removes redundant lyric website mentions of artist/song title/album	   #
#   - changes “â€™” to “’” which comes up way too often in downloaded lyrics   #
#   - Removes special command-line characters if in -1 mode					   #
#   - Removes leading comma from lines that start with a comma				   #
################################################################################




###########  CONSTANTS: BEGIN:  ###########
my $ADDED_END_LINE_CHARACTER    = ".";					#character to append to each line of lyrics, since people don't typically add periods or commas to the end of posted lyrics online. Without adding a “phantom period” to the end of each line, WhisperAI’s ‘--sentence’ parameter will not function correclty, and awkward transcriptions are generated where multiple lines of lyrics are one one line of transcriptino
###########  CONSTANTS: ^^END^  ###########

# libraries
use strict;
use warnings;
use utf8;												# enable processing of modern character sets
use Encode qw(decode FB_CROAK);
binmode(STDOUT, ":encoding(UTF-8)");					# output real UTF-8
binmode(STDERR, ":encoding(UTF-8)");					# error output real UTF-8
binmode(STDIN , ":raw");								# input must arrive as raw bytes so WE can decode it safely
use Encode::Guess;
use FindBin;
use lib $FindBin::Bin;
use LimitRepeats;
use WhisperAIProcessing;	
use BulletproofFileReading;
use LyricsProcessing;
use SmartQuotes;
use CharacterEncodingFlaws;
use CommandLine;

# Default modes:
my $LYRICS_MODE         = 1;							# default mode
my $ONE_LINE            = 0;							# default mode
my $UNIQUE_LINES_MODE   = 0;							# default mode
my $ADD_CHARACTER_MODE  = 1;							# default mode
my $SMART_QUOTE_CONVERT = 1;							# default mode - we did not add a command-line way to change out of this mode



# Extract filename if present (not a switch), then process remaining options
my $filename = "";
my @options;
foreach my $arg (@ARGV) {
	if (-f $arg && $arg !~ /^-/) {
		$filename = $arg;
	} else {
		push @options, $arg;
	}
}


# Now process the remaining options:
@ARGV = @options;  # Restore only options to @ARGV

foreach my $arg (@ARGV) {
	if    ($arg eq '-1') { $ONE_LINE           = 1; }
	elsif ($arg eq '-0') { $ONE_LINE           = 0; }
	elsif ($arg eq '-L') { $LYRICS_MODE        = 1; }
	elsif ($arg eq '-N') { $LYRICS_MODE        = 0; }
	elsif ($arg eq '-A') { $UNIQUE_LINES_MODE  = 0; }
	elsif ($arg eq '-U') { $UNIQUE_LINES_MODE  = 1; }
	elsif ($arg eq '-P') { $ADD_CHARACTER_MODE = 1; }
	elsif ($arg eq '-S') { $ADD_CHARACTER_MODE = 0; }
	elsif ($arg eq '-H') { show_usage();    exit 1; }
	else                 { show_usage();    exit 1;	}
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
my $file_itle="";
my $file_album="";
my $original_line;
my $file_orig_artist;
my $i="";
         
# grab some values from the environment, if they happen to be in there. They can provide additional information used to massage lyrics.				  
if ($LYRICS_MODE) {
	$file_artist      = $ENV{FILE_ARTIST}      || "";		# grab some values from the environment, if appropriate environment variables set
	$file_orig_artist = $ENV{FILE_ORIG_ARTIST} || "";		# grab some values from the environment, if appropriate environment variables set
	$file_title       = $ENV{FILE_TITLE }      || "";		# grab some values from the environment, if appropriate environment variables set
	$file_album       = $ENV{ALBUM      }      || "";		# grab some values from the environment, if appropriate environment variables set
}
#my $do_it=-1;
my $line_number=0;


$file_itle=$file_title;
$file_itle=~s/^.(.*)$/$1/;

use Encode qw(decode FB_DEFAULT FB_CROAK FB_QUIET FB_WARN);
use Encode::Guess;
my $INPUT;
if ($filename eq "") {
	$INPUT = *STDIN;
} else {
	#pen($INPUT, "<:utf8", $filename) or die "💥 lyric-postprocessor could not open file '$filename': $!";		# breaks on malformed files, of which there are many
	#pen($INPUT, "<:raw" , $filename) or die "💥 lyric-postprocessor could not open file '$filename': $!";		# open raw, and decode to UTF-8 later after fixing malformed characters
	#pen($INPUT, "<:utf8", $filename) or die "💥 lyric-postprocessor could not open file '$filename': $!";		# breaks on malformed files, of which there are many
	open($INPUT, "<:raw" , $filename) or die "💥 lyric-postprocessor could not open file '$filename': $!";
}



## RAN FOR YEARS, NUKED 20260410:       while (<$INPUT>) {
## RAN FOR YEARS, NUKED 20260410:       	my $raw       = $_;
## RAN FOR YEARS, NUKED 20260410:       	my $line      = $_;
## RAN FOR YEARS, NUKED 20260410:       	my $line_orig = $_;
## RAN FOR YEARS, NUKED 20260410:       	#$raw     =~ s/\xA0/ /g;																	# Replace non-breaking space, which crashes us on various input files
## RAN FOR YEARS, NUKED 20260410:       	#$line =~ s/\xA0/ /g;	
## RAN FOR YEARS, NUKED 20260410:       	#$line =  decode('UTF-8', $raw, Encode::FB_CROAK | Encode::LEAVE_SRC);
## RAN FOR YEARS, NUKED 20260410:           #eval { $line = decode('UTF-8', $raw, FB_CROAK); };    # Try UTF-8 first        # If UTF-8 fails, fallback to Latin-1 (Windows-1252)
## RAN FOR YEARS, NUKED 20260410:           #if ($@) { eval    { $line = decode('Windows-1252', $raw, FB_CROAK   ); };
## RAN FOR YEARS, NUKED 20260410:           #          if ($@) { $line = decode('UTF-8'       , $raw, FB_HTMLCREF); warn "Warning: sanitized malformed line: $.\n"; } }	# As last resort, decode and replace problematic bytes with HTML entities
## RAN FOR YEARS, NUKED 20260410:           #my $decoder = Encode::Guess->guess($raw);       # If guessing fails, default to Latin1 and log a warning
## RAN FOR YEARS, NUKED 20260410:           #if (ref($decoder)) { $line = $decoder->decode($raw); } else { warn "Encoding guess failed at line $.: $decoder\n"; $line = decode("Windows-1252", $raw); }
## RAN FOR YEARS, NUKED 20260410:           #$line =~ s/\x{A0}/ /g;							# Replace non-breaking spaces
## RAN FOR YEARS, NUKED 20260410:           #$line =~ s/[^\x09\x0A\x0D\x20-\x7E]//g;			# Strip non-printables except tab/newline
## RAN FOR YEARS, NUKED 20260410:           # Continue your existing processing...
## RAN FOR YEARS, NUKED 20260410:       
## RAN FOR YEARS, NUKED 20260410:       	#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ FILE IS SAFELY OPEN NOW! GEEZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## RAN FOR hours, NUKED 20260410:       	# First try real UTF-8. If that fails, fall back to Windows-1252,
## RAN FOR hours, NUKED 20260410:       	# which is what a ton of lyric files actually are in practice.
## RAN FOR hours, NUKED 20260410:       	eval {
## RAN FOR hours, NUKED 20260410:       		$line = decode('UTF-8', $raw, FB_CROAK);
## RAN FOR hours, NUKED 20260410:       		1;
## RAN FOR hours, NUKED 20260410:       	} or eval {
## RAN FOR hours, NUKED 20260410:       		$line = decode('Windows-1252', $raw, FB_CROAK);
## RAN FOR hours, NUKED 20260410:       		1;
## RAN FOR hours, NUKED 20260410:       	} or eval {
## RAN FOR hours, NUKED 20260410:       		$line = $line_orig;
## RAN FOR hours, NUKED 20260410:       	} or die "lyric-postprocessor.pl Could not decode input at line $. as UTF-8 or Windows-1252\n";

## RAN FOR YEARS, NUKED 20260410:       	$line =~ s/\n/ /ig;		#get rid of newline
## RAN FOR YEARS, NUKED 20260410:       	# Keep track of line, line number, original/untouched line (becuase we’re finna touch it)
## RAN FOR YEARS, NUKED 20260410:       	$line_number++;
## RAN FOR YEARS, NUKED 20260410:       	my $original_line=$line;


while (my $raw = <$INPUT>) {
	my $line = decode_mixed_line($raw);

	# On raw input, chomp may leave \r behind on CRLF files, so strip line ending explicitly.
	$line =~ s/\r?\n\z/ /;
	$line =~ s/[\r\n]+/ /g;
	$line =~ s/\n/ /ig;


	$line_number++;
	my $original_line = $line;

	if ($SMART_QUOTE_CONVERT) {  $line = replace_smart_quotes($line); }		# convert dumb quotes ("") to smart quotes (“”)
	if ($LYRICS_MODE) {
		#pre-processing
		$line =~ s/ +$//;					#remove trailing spaces

		#first-line-only stuff to red rid of
		if ($line_number == 1) {
			#line =~ s/(\d)([^\d]+)/$2/;		#remove  only 1 leading digit  from 1ˢᵗ line if it's just a single digit 'cause I've noticed that happens a lot
			$line =~ s/(\d{1-3})([^\d]+)/$2/;	#remove up to 3 leading digits from 1ˢᵗ line [2 weren't enough!]
		}

		#website spam: divider lines to get rid of
		$line =~ s/^-+//;					#get rid of lines like: ---------------

		#website spam: song sections to get rid of
		for ($i=1; $i<=2; $i++) {			#twice to get things like "Intro/Chorus" or "Guitar Solo/Bridge", which meant changing the regex to include an ending of / where previously it just included ]
			#line =~    s/[\[\(]?(Intro|Sample|Hook|Verse|Pre\-Chorus|Refrain|Chorus|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Bridge|Interlude|False Ending|Outro) *\d*:* *[\w \-&'",]*[\]\)\/]?//i;
			#line =~    s/[\[\(]? ?(Spoken|Whispered|Sample|Sample \d+|Intro|Intro \d+|Hook|Build:? ?[a-z &]+|Verse|Verse +\d|Pre\-Chorus|Refrain|Refrain +\d|Drop|Chorus|Chorus \d|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Solo +\d+|Bridge|Instrumental Interlude|Interlude|False Ending|Outro)[\.]* *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;

			#2025/05/18: adding “^” at beginning of this regex so that it doesn’t get things in mid-line
				#because in c:\new\MUSIC\They Might Be Giants\Compilations\They Might Be Giants - 2002 - Dial-A-Song. 20 Years of They Might Be Giants (2CD)\Disc 2\2_16_Robot Parade (Adult Version).txt
				#the line “To build a giant cyborg” got turnedi nto “To”

			$line =~   s/^[\[\(]? ?(Spoken|Whispered|Sample|Sample \d+|Intro|Intro \d+|Hook|Build:? ?[a-z &]+|Verse|Verse +\d|Pre\-Chorus|Refrain|Refrain +\d|Drop|Chorus|Chorus \d|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Solo +\d+|Bridge|Instrumental Interlude|Interlude|False Ending|Outro)[\.]* *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;
			#line =~ s/\d?[\[\(]? ?(Spoken|Whispered|Sample|Sample \d+|Intro|Intro \d+|Hook|Build:? ?[a-z &]+|Verse|Verse +\d|Pre\-Chorus|Refrain|Refrain +\d|Drop|Chorus|Chorus \d|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Solo +\d+|Bridge|Instrumental Interlude|Interlude|False Ending|Outro)[\.]* *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;
			#2025/05/18 removing the “?” after “\d” so that it only applies if an errant digit is before it:
			$line =~ s /\d[\[\(]? ?(Spoken|Whispered|Sample|Sample \d+|Intro|Intro \d+|Hook|Build:? ?[a-z &]+|Verse|Verse +\d|Pre\-Chorus|Refrain|Refrain +\d|Drop|Chorus|Chorus \d|Post\-Chorus|Instrumental (Intro|Break|Outro)|Breakdown|Solo|[\da-z]+ Solo|Solo +\d+|Bridge|Instrumental Interlude|Interlude|False Ending|Outro)[\.]* *\d*:* *[\w \-&'",]* *[\]\)\/]?//i;
			#SOLVED:  "This is a real good chorus." gets transformed to "This is really good" .. so 2025/05/14: adding [\.]* after |Outro)
		}




		#word corrections
		$line =~ s/^(.*[a-zA-Z])Embed\.?$/$1/i;			#the word “Embed” is sometimes tacked onto the end of a line of downloaded lyrics:
		$line =~ s/our selves/ourselves/g;	



		################ LINE-BASED FIXES: ################
		for my $re (@hallucination_patterns) { $line =~ s/$re//g; }

		#website spam to get rid of
		#$line =~ s/^(.*[a-zA-Z])Embed\.?$/$1/i;														# common junk found in downloaded lyrics
		#$line =~ s/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used//i;
        #$line =~ s/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+//i;
        #$line =~ s/\*? ?Downloaded from: http:\/\/[^ ]+//i;
		#$line =~ s/Album tracklist with lyrics//;
		#$line =~ s/You might also like//i;
		#$line =~ s/^[0-9] Contributors$//;
		#$line =~ s/^.* Lyrics$//;							# todo we could be probing and using the songtitle here to be more restrictive
		#$line =~ s/Get tickets as low as \$[\d\.]+//i;
		for my $re (@lyric_website_spam_patterns) { $line =~ s/$re//g; }




		#### artist/song mentions to get rid of:
		#dynamic content removals {uses environment variables set in create-lyrics bat}		
		if ($file_artist ne "") { 
			$line =~ s/See \Q$file_artist Live\E//i; 
			$line =~ s/Artist: \Q$file_artist\E[\.,]?//i; 
		}
		if ($file_title ne "") { 
			$line =~ s/Title: \Q$file_title\E[\.,]?//i; 
			$line =~ s/\Q$file_title\E Lyrics//i; 			
		}
		if ($file_title ne "") {
			$line =~ s/\Q$file_itle\E Lyrics//i; 			
		}
		if ($file_album ne "") { 
			$line =~ s/Album: \Q$file_album\E[\.,]?//i; 
		}
		$line =~ s/^Lyrics by .*$//;

		#however our environment variables aren’t always set, 
		#so we ended up needing to do this more aggressively:
		$line =~  s/^Album: [\w\s]+\.?$//i; 
		$line =~  s/^Title: [\w\s]+\.?$//i; 
		$line =~ s/^Artist: [\w\s]+\.?$//i; 
		$line =~     s/^id: [\w\s]+\.?$//i; 



		#line-level fixes:
		$line =~ s/^, *$//;			#remove leading comma like ", a line of text"

		#character-level fixes: commas and quotes and dashes and punctuation, oh my!
		#$line =~ s/[â′'`]/’/ig;			# apostrophes and misrepresentations thereof
		#$line =~ s/â€™/’/ig;			# apostrophes and misrepresentations thereof (kludge 20250424 1358)
		#$line =~ s/€™/’/ig;
		##$line =~ s/’’/’/ig;				# apostrophes and misrepresentations thereof (kludge 20250424 1358)
		#OLD: $line =~ s/\-\-/—/g;		# fix “--” which is an archaic way of representing “—” ... Although this really should be turned into “——” if we are in a monospaced situation
		#$line =~ s/\-\-([^>])/—$1/g;	# fix “--” which is an archaic way of representing “—” ... Although this really should be turned into “——” if we are in a monospaced situation
		#$line =~ s/„/”/g;				# copied from WhisperAIProcessing.pm: this is how Germans OPEN quotes („like this”), and we’re not German, so we convert „ to “
		$line = &fix_common_character_encoding_flaws($line);
		

		#character-level fixes for command line compatibility: because our lyrics become part of a command-line prompt to WhisperAI:
		#$line =~ s/\|/│/g;				# because our lyrics hit the command line, we need to ensure redirection characters not reach our command-line, which is what our lyrics mode is used for		
	    #$line =~ s/"/'/g;				# change quotes to apostrophes so these can be used as a quoted command line argument
		#$line =~ s/</⧼/g;				# redirection characters should not reach our command-line, which is what our lyrics mode is used for
		#$line =~ s/>/⧽/g;				# redirection characters should not reach our command-line, which is what our lyrics mode is used for
		$line = &fix_invalid_command_line_characters($line);

		# word level fixes
		$line =~ s/([a-z]) (\-)([a-z])/$1$2$3/ig;												   # turn things like “double -dutch” back into “double-dutch”
		$line =~ s/\bwont\b/won’t/gi;

		#formatting: dealing with ALL CAPS LYRICS
		#if there are >=10 all-caps letters and no lowercase letters, lowercase the line
		if (($line =~ /[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z].*[A-Z]/) && ($line !~ /[a-z]/)) {
			$line = lc($line);
		}

		#fix crap like: “ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo”
		$line = &limit_repeats($line, $MAX_KARAOKE_WIDTH_MINUS_ONE - 4);  

		#clean leading/trailing spaces
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
		#Removed 20260429 code cleanup: $to_print  =~ s/’’/’/ig;	#kludge added 20250424 1358 copied here 20250505 1833
		$to_print .=  " ";
	} else { 
		if (($to_print eq "") && ($to_print_last eq "")) {
			# (do nothing)
		} else {
			$to_print .= "\n";
		}
	}

	# store only if unique, postprocess later
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
$lines[-1] =~ s/,$// if @lines;								# Remove the comma from the last line if it exists
my $output="";
if ($ONE_LINE) {
    my $final_output = join('', @lines);				    # Join all lines into a single string and remove the trailing comma if it exists
    $final_output =~ s/, +$//;								# Remove the last trailing “,” [comma] if it exists
    $final_output =~ s/^\d\.? ?//;							# Remove “1. ”-type stuff at beginning
	#$final_output =~ s/\f|/│/;								# Remove pipe symbol because of command-line issues it creates and it not being anything we’d ever want in an AI-prompt particularly because it’s invalid on the command line without setdos pre/postfixing
    print $final_output;
} else {													# postprocessing for when lines are together:
    $lines[-1] =~ s/, *$// if @lines;					    # Remove the comma from the last line if it exists
    foreach my $line (@lines) { $output .= $line; }		    # Print all lines
}
print $output;

sub show_usage {
	print "\n ***** USAGE: *****\n\n";
	print   "    type filename.txt |  lyric-postprocessor {flags}\n";
	print "\n           ---OR--- \n\n";
	print   "    lyric-postprocessor {flags} filename.txt\n";
	print "\n           ---OR--- \n\n";
	print   "    lyric-postprocessor filename.txt {flags}\n\n\n";
	print "\n ***** FLAGS: ***** \n\n";
	print   "    lyric-postprocessor -A -- print only unique lines: OFF [default]\n";
	print   "    lyric-postprocessor -U -- print only unique lines: ON\n";
	print   "    lyric-postprocessor -N -- lyric postprocessing mode OFF [default]\n";
	print   "    lyric-postprocessor -L -- lyric postprocessing mode ON\n";
	print   "    lyric-postprocessor -0 -- smush into one line: OFF [default]\n";
	print   "    lyric-postprocessor -1 -- smush into one line: ON\n";
	print   "    lyric-postprocessor -P -- add “$ADDED_END_LINE_CHARACTER” character to end of line: ON [default]\n";
	print   "    lyric-postprocessor -S -- add “$ADDED_END_LINE_CHARACTER” character to end of line: OFF\n";
	print "\n **** NOTE: **** \n";
	print   "      * Adds “$ADDED_END_LINE_CHARACTER” to the end of each line by default, for better WhisperAI parsing with the --sentence option\n";
	print   "      * Changes \' into \’\n";	
	print   "      * Converts ALL-CAPS lyrics to not be all caps\n";	
	print   "      * Shortens lines like “OOOOOOOOOOOOOOOOOOOOOOOOOOOO” to be no longer than %MAX_KARAOKE_WIDTH_MINUS_ONE% characters\n";	
	print   "      * Removes song-section titles like “[chorus]” \n";	  #TODO but maybe this should only be for -1 mode?
	print   "      * Removes lyric website advertising spam that inserts itself into the results\n";	
	print   "      * Removes redundant lyric website mentions of artist/song title/album\n";	
	print   "      * Removes special command-line characters if in smushing-into-one-line mode (“-1”)\n";	
	print   "      * Removes divider lines like “-------”\n";	
	print   "      * Removes leading comma from lines that start with a comma\n\n";	
}

