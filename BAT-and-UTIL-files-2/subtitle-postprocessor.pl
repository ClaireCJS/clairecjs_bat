#############################################################################################################################################
#############################################################################################################################################
#############################################################################################################################################
#####																																	#####
#####                               █████   ███ ███  ██████   ███████  █████  ███████  █████    ███████									#####   ✨ ✨ ✨ ✨ ✨ ✨ NOTE ✨ ✨ ✨ ✨ ✨ ✨    
#####                              █     █   █   █    █    █  █  █  █    █    █  █  █    █       █    █									#####                                             
#####                              █         █   █    █    █     █       █       █       █       █										#####                                             
#####                              █         █   █    █    █     █       █       █       █       █  █									#####   This was written as a companion piece     
#####                               █████    █   █    █████      █       █       █       █       ████									#####   to lyric-postprocessor.pl                 
#####                                    █   █   █    █    █     █       █       █       █       █  █									#####                                             
#####                                    █   █   █    █    █     █       █       █       █       █										#####   As such, there are many corrections       
#####                              █     █   █   █    █    █     █       █       █       █   █   █    █									#####   made in lyric-postprocessor that are      
#####                               █████     ███    ██████     ███    █████    ███    ███████  ███████									#####   NOT made in subtitle-postprocessor        
#####  																																	#####                                             
#####  																																	#####   The intended workflow is to use BOTH,     
#####  																																	#####   so some of the use cases that are         
#####  																																	#####   properly processed by the workflow as     
#####    ██████     ███     █████   ███████        ██████   ██████     ███      ████   ███████   █████    █████     ███   ██████		#####   a whole may not be properly processed     
#####     █    █   █   █   █     █  █  █  █         █    █   █    █   █   █    █    █   █    █  █     █  █     █   █   █   █    █		#####   if you only use 1 piece or another        
#####     █    █  █     █  █           █            █    █   █    █  █     █  █         █       █        █        █     █  █    █		#####                                             
#####     █    █  █     █  █           █            █    █   █    █  █     █  █         █  █    █        █        █     █  █    █		#####   A valid way of coping with this is to     
#####     █████   █     █   █████      █            █████    █████   █     █  █         ████     █████    █████   █     █  █████		#####   duplicate the code in both scripts ——     
#####     █       █     █        █     █   ███████  █        █  █    █     █  █         █  █          █        █  █     █  █  █			#####   To some extent, this has been done.       
#####     █       █     █        █     █            █        █  ██   █     █  █         █             █        █  █     █  █  ██		#####                                             
#####     █        █   █   █     █     █            █        █   █    █   █    █    █   █    █  █     █  █     █   █   █   █   █		#####   But we are never claming 100％ on this.   
#####    ████       ███     █████     ███          ████     ███  ██    ███      ████   ███████   █████    █████     ███   ███  ██		##### 
#####																																	#####  
#############################################################################################################################################
#############################################################################################################################################
#############################################################################################################################################

#!/usr/bin/env perl                                                                                    # Specify the script interpreter
use strict;                                                                                            # Enforce strict variable declaration rules
use warnings;                                                                                          # Display warnings for potential errors
use File::Copy qw(move);                                                                               # Import move() for replacing files
use utf8;                                                                                              # enable UTF-8 character support
binmode(STDOUT, ":utf8");																			   # enable UTF-8 character support on standard out
binmode(STDIN , ":utf8");																			   # enable UTF-8 character support on standard in
binmode(STDERR, ":utf8");																			   # enable UTF-8 character support on standard err
use FindBin;
use lib $FindBin::Bin;
use DeCensor;
use LimitRepeats;
use WhisperAIProcessing;
use AbbreviatedWords;

################################################################################################################################################################################################################################################

################################## CONFIG: SUIBTITLE-SPECIFIC CONFIG: ################################## 

my $LEAVE_CENSORSHIP                    =  0;								 # Set to 0 to de-censor things, set to 1 to leave things censored
my $REMOVE_PERIODS                      =  1;                                # Remove a single trailing period (and spaces) including our “invisible periods” (that aren’t really invisible) which we deliberately place into our lyrics to force WhisperAI’s “--sentence” option to correctly process line breaks in a way that makes semantic sense
my $USE_WORDS_MODE                      =  1;                                # Checks for words that end in a period before removing periods from the end of each line
#  $MAX_KARAOKE_WIDTH_MINUS_ONE         = 24;								 # This system aims for a max width of 25
#  $MAX_KARAOKE_WIDTH_MINUS_ONE_TIMES_2 = $MAX_KARAOKE_WIDTH_MINUS_ONE * 2;  # used for formatting


################################################################################################################################################################################################################################################



###### SET INITIAL FLAGS: ######################################################################################################################################################################################################################

my $do_test_suite = 0;
my $filename;                                                                                          # Variable to hold the input file name
my $tmpLine;

###### PARSE COMMAND-LINE PARAMETERS: ##########################################################################################################################################################################################################

my $arg;
foreach $arg (@ARGV) {                                                                                 # Iterate over command-line arguments		#DEBUG: print "checking arg $arg\n";
    if    ($arg eq "-t" || $arg eq "--test"                           ) { $do_test_suite    = 1; }     # Check if —t or ——test             was passed; Run test suite if it was
    elsif ($arg eq "-w" || $arg eq "--wordsw" || $arg eq "--WhisperAI") { $USE_WORDS_MODE   = 1; }     # Check if —w or ——words            was passed; Enable words mode if it was                                                                                
    elsif ($arg eq "-l" || $arg eq "--leave_censorship"               ) { $LEAVE_CENSORSHIP = 1; }     # Check if —l or ——leave_censorship was passed; Enable decensoring mode if it was                                                                                 
    elsif ($arg =~ /^(\-\-?|\/?)he?l?p?$/i)                             { &usage();        exit; }     # Provide usage directions in response to common help flags
    elsif (!$filename)                                                  { $filename    =   $arg; }     # Treat the first non-flag argument as the file name
}

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Test-suite-only mode
# —————————————————————————————————————————————————————————————————————————————————————————————————————

if ($do_test_suite) {
	&decensorship_test_suite;
	exit;
}

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Validate the input file.
# —————————————————————————————————————————————————————————————————————————————————————————————————————

if (   !$filename) {                                                                                   # Ensure a file name was provided
    die "Error: No file specified.\nUse --help for usage instructions.\n";                             # Exit with error if no file is specified
}
if (!-e $filename) {                                                                                   # Check if the file exists
    die "Error: File '$filename' does not exist.\n";                                                   # Exit with error if the file does not exist
}

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Execute the program logic based on the selected mode.
# If words mode is active, load an exception list and handle advanced cases.
# Otherwise, perform a simple end-of-line period removal.
# The modifications are written back to the file inline.
# —————————————————————————————————————————————————————————————————————————————————————————————————————

my $tempfile = "$filename.tmp";                                                                        # Temporary file to write modifications
open my $in , '<:encoding(UTF-8)', $filename or die "Error: Cannot open input " .  "file: $!\n";       # Open the file for reading with UTF-8 encoding
open my $out, '>:encoding(UTF-8)', $tempfile or die "Error: Cannot create temporary file: $!\n";       # Open the temporary file for writing with UTF-8 encoding

################################################################################################################################################################################################################################################

# Vanity and trolling:
my @greplines = <$in>;
my $already_has_vanity = grep { /^\Q# Generated by Claire\E\s*$/ } @greplines;
if (!$already_has_vanity) {
	print $out                                "\n";
	print $out "# Generated by Claire"      . "\n";
	print $out "# Sawyer’s WhisperAI-based" . "\n";
	print $out "# transcription system."    . "\n";
	print $out "# Kill yourself, Trumpers." . "\n";
	print $out                                "\n";
}


################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

# Read the whole file into memory to pre-process malformed SRTs
seek($in, 0, 0);                    # Rewind the input filehandle
my @fixed;
my @lines     = <$in>;
my $block_num = 1;
my $state     = 'start';
my $buffer    = '';

foreach my $line (@lines) {
    chomp($line);

    if ($line =~ /^\s*#/) {
        push @fixed, $line;
        next;
    }

    next if $state eq 'start' && $line !~ /^\d\d:\d\d:\d\d,\d{3} --> \d\d:\d\d:\d\d,\d{3}$/;

	if ($line =~ /^\d\d:\d\d:\d\d,\d{3} --> \d\d:\d\d:\d\d,\d{3}$/) {
		if ($buffer ne '') {
			my @buf_lines = split(/\n/, $buffer);
			my $text_found = grep { $_ !~ /^\d\d:\d\d:\d\d,\d{3} --> \d\d:\d\d:\d\d,\d{3}$/ && $_ !~ /^\s*$/ } @buf_lines;
			if ($text_found) {
				push @fixed, "$block_num";
				push @fixed, @buf_lines;
				push @fixed, '';
				$block_num++;
			}
		}
		$buffer = "$line\n";
		$state = 'text';
	}
    elsif ($state eq 'text') {
        next if $line =~ /^\d+$/;   # 💥 This line removes duplicate block numbers
        $buffer .= "$line\n";
    }
}

# Flush last buffer
if ($buffer ne '') {
    my @buf_lines = split(/\n/, $buffer);
    my $text_found = grep { $_ !~ /^\d\d:\d\d:\d\d,\d{3} --> \d\d:\d\d:\d\d,\d{3}$/ && $_ !~ /^\s*$/ } @buf_lines;
    if ($text_found) {
        push @fixed, "$block_num";
        push @fixed, @buf_lines;
        push @fixed, '';
        $block_num++;
    }
}






# Now @fixed contains the cleaned-up subtitle lines.





if ($USE_WORDS_MODE) {                                                                                 # If words mode is enabled
    # Define a list of common exceptions where periods are preserved                                 									
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    # Words mode processing loop:
    # - Preserve ellipses ("...")
    # - Preserve periods in exceptions
    # - Remove other end-of-line periods
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    foreach $_ (@fixed) {																			   # Read the file line by line
        chomp;                                                                                         # Remove the newline for safer processing
		$tmpLine = &whisper_ai_postprocess($_,$LEAVE_CENSORSHIP,$REMOVE_PERIODS);
        print $out  "$tmpLine\n";                                                                      # Print the modified line to the output file
    }																							 	   
} else {                                                                                               # Default mode: blind period removal
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    # Simple mode processing loop:
    # - Remove exactly one period from the end of the line and does nothign else
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    foreach $_ (@fixed) {																			   # Read the file line by line
        chomp;                                                                                         # Remove the newline for safer processing
		#maybe not anymore!: $tmpLine = &whisper_ai_postprocess($_,$LEAVE_CENSORSHIP,$REMOVE_PERIODS); # don’t do our special WhisperAI-specific processing!
		$tmpLine = $_;
        $tmpLine =~ s/\.\s*$//;                                                                        # Remove exactly one trailing period —— because these are the “invisible periods” we add to the end of each line of downloaded lyrics, which cause WhisperAI’s --sentence parameter to work properly [vs improperly if you don’t add the “invisible” periods to the end of each line]																									   # do nothing else!
        print $out "$tmpLine\n";                                                                       # Print the modified line to the output file
    }
}

close $in  or die "Error: Cannot close input file: "     . "$!\n";                                     # Close the input file
close $out or die "Error: Cannot close temporary file: " . "$!\n";                                     # Close the temporary file
move $tempfile, $filename or die "Error: Cannot overwrite original file: $!\n";                        # Replace the original file with the temporary file

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

sub usage {
	print <<'USAGE';                                                                               # Print usage instructions and exit
    Usage: perl subtitle-postprocessor.pl [options] <file>
    
    Options:
      -w, --WhisperAI, --words      Enable advanced processing mode (created with WhisperAI-transcribed audio in mind)
      -L, --leave_censorship        Disable the uncensoring of censored words
      -h, --help, -h, ?, /?, help   Display this help message.

      -t, --test                    Run test suite
    
    👿👿👿👿👿 WARNING: This script modifies the file inline! Hope you have a backup! 👿👿👿👿👿
    
    Description:
        Default  mode:                 Removes exactly one period from the end of each line, no exceptions.
        Advanced mode (--words, -w):   Preserves periods in common abbreviations (e.g., "Mr.", "Dr.") and ellipses ("..."),
		                               decensors c*ensor*d w*rds, fixes bad character encoding, too-many-times-repeated characters
		                               fixes mis-hyphenated words, removes WhisperAI-specific hallucinations, removes lyric website spam
USAGE
    exit;                                                                                          # Exit after showing usage information
}

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################






### sub whisper_ai_postprocess {
### 	my $s=$_[0];
### 	
### 	################ CHAR-BASED CHARACTER FIXES: ############### 
### 	$s = &limit_repeats($s, $MAX_KARAOKE_WIDTH_MINUS_ONE - 4);								                             # Fix lines like “Noooooooooooooooooooooooooooooooooooo” from being wider than our subtitle length
### 	$s =~ s/\-\-([^>])/—$1/g;																	                         # fix “--” which is an archaic way of representing “—” ... Although this really should be turned into “——” if we are in a monospaced situation
### 	$s =~ s/[â′'`]/’/ig;																		                         # not-smart apostrophes and misrepresentations thereof
### 	$s =~ s/â€™/’/g;
### 	$s =~ s/€™/’/g;
### 	$s =~ s/!“/!”/g;																			                         # copied from lyric-postprocessor: kludge bug fix
### 	$s =~ s/„/”/g;
### 	#$s =~ s/’’/’/g;
### 	$s =~ s/^†/“/g;																										 #\__  WhisperAI keeps using the † symbol instead of “ for some reason
### 	$s =~ s/ †/ “/g;																									 #/
### 
### 																						                            
### 																							                            
### 	################ WORD-BASED PUNCTUATION FIXES: ################ 							                         
### 	$s =~ s/self \-righteous/self-righteous/g;													                         # 1)    proof of concept: fix hyphenated words that have an erroneous space before the hyphen
### 	$s =~ s/([a-z]) (\-)([a-z])/$1$2$3/ig;														                         # 2) generalized version: turn things like “double -dutch” back into “double-dutch”, since Whisper AI seems to do this
### 																							                            
### 	################ WORD-BASED WORD FIXES: ################ 								                            
### 	$s =~ s/our selves/ourselves/g;														                                 # common grammatical mistake
### 	$s =~ s/\bwont\b/won’t/gi;																                            
### 																							                            
### 	################ LINE-BASED FIXES: ################ 									                            
### 	if (!$LEAVE_CENSORSHIP) { $s =  &de_censor($s); }  																	# remove censorship —— see —t option for testing the decensoring code
### 																							                            
### 	################ LINE-BASED FIXES: WHISPER-AI HALLUCATIONS ################
### 	for my $re (@hallucination_patterns) { $s =~ s/$re//gi; }
### 	$s =~ s/Thank you for watching[\.!]*//ig;																			  # 202604: this one keeps showing up so trying to fix it a second time as a kludge
### 	
### 	################ LINE-BASED FIXES: LYRIC WEBSITE SPAM: ################						# If our code was more honest, this would be in a separate function as it’s not *directly* related to WhisperAI postprocessing, and more of an artifact of downloading lyrics from websites with autodownloaders like “LyricsGenius.exe”
### 	$s =~ s/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used//i;
### 	$s =~ s/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+//i;
### 	$s =~ s/\*? ?Downloaded from: http:\/\/[^ ]+//i;
### 	$s =~ s/Get tickets as low as \$[\d\.]+//i;
### 	$s =~ s/Album tracklist with lyrics//;
### 	$s =~ s/^(.*[a-zA-Z])Embed\.?$/$1/i;														# common junk found in downloaded lyrics
### 	$s =~ s/You might also like//i;																# common junk found in downloaded lyrics
### 
### 	########## LINE-BASED PUNCTUATION FIXES: RELATED TO MY AI-MUSIC-TRANSCRIPTION SYSTEM: ########## 
### 	$s =~ s/^, *$//;																		    # remove leading comma like “, a line of text”
### 	if ($REMOVE_PERIODS == 1) {	
### 			if    ( $s =~ /\.\.\.\s*$/) { $s =~ s/\.\.\.\.$/.../; }                             # Check if line ends with ellipses (“..."), if so, don’t use our period-removal code, but DO change a line ending in “....” to “...”
### 			elsif ( $s =~ /(\b(?:$period_removal_exceptions_regex))\.\s*$/i) { }                               # Otherwise, check if the line ends with a recognized exception (“Ms.”)
### 			else  { $s =~ s/\.\s*$//;}															# Remove a single trailing period (and spaces) including our “invisible periods”
### 	}                                                
### 		  
### 	return($s);
### }
### 
### 
### 

