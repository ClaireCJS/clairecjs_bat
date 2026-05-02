#!/usr/bin/env perl                                                                                    # Specify the script interpreter



###   This was written to process *DOWNLOADED* LRC files, inline -- no temp files; changes are overwritten



##### LIBRARIES: #######################################################################################################################

use strict;                                                                                            # Enforce strict variable declaration rules
use warnings;                                                                                          # Display warnings for potential errors
use File::Copy qw(move);                                                                               # Import move() for replacing files
use utf8;                                                                                              # enable UTF-8 character support
use FindBin;
use lib $FindBin::Bin;
#use DeCensor;
#use LimitRepeats;
use WhisperAIProcessing;	
use BulletproofFileReading;


##### CONFIG: LRC-SPECIFIC CONFIG: #################################################################################################

my $LEAVE_CENSORSHIP       =  0;                  # Set to 0 to de-censor things, set to 1 to leave things censored
my $USE_WORDS_MODE         =  1;                  # Use full lyric/WhisperAI-style postprocessing instead of only removing final periods
my @LRC_patterns_to_delete =  (                   # stuff we want taken out of downloaded LRC files but not out of TXT/SRT files
		# (currently empty)
);



###### PARSE COMMAND-LINE PARAMETERS: ##########################################################################################################################################################################################################

my $arg;
my $filename;                                                                                          # Variable to hold the input file name
my $do_test_suite=0;
foreach $arg (@ARGV) {                                                                                 # Iterate over command-line arguments
    if    ($arg eq "-t" || $arg eq "--test"                           ) { $do_test_suite    = 1; }     # Run test suite
    elsif ($arg eq "-w" || $arg eq "--words" || $arg eq "--WhisperAI")  { $USE_WORDS_MODE   = 1; }     # Enable words mode
    elsif ($arg eq "-s" || $arg eq "--simple"                         ) { $USE_WORDS_MODE   = 0; }     # Disable words mode; only remove final periods
    elsif ($arg eq "-l" || $arg eq "--leave_censorship"               ) { $LEAVE_CENSORSHIP = 1; }     # Leave censored words alone
    elsif ($arg =~ /^(\-\-?|\/?)he?l?p?$/i)                             { &dlrcpusage();   exit; }     # Provide usage directions
    elsif (!$filename)                                                  { $filename   =    $arg; }     # Treat first non-flag argument as filename
}


##### TEST SUITE: ##############################################################################################################################################################################################################################

if ($do_test_suite) { &do_test_suite; exit; }


##### VALIDATE INPUT FILE: #####################################################################################################################################################################################################################

my   $read_from_stdin = (!defined($filename) || $filename eq '-');
if (!$read_from_stdin && !-e $filename) { die "Error: File '$filename' does not exist.\n"; }



##### OPEN OUTPUT FILE: #####################################################################################################################################################################################################################

binmode(STDOUT, ":utf8");                                                                              # enable UTF-8 character support on standard out
binmode(STDIN , ":utf8");                                                                              # enable UTF-8 character support on standard in
binmode(STDERR, ":utf8");                                                                              # enable UTF-8 character support on standard err

my $in;
my $out;
my $tempfile;

if ($read_from_stdin) {
    $in  = \*STDIN;
    $out = \*STDOUT;
} else {
	$tempfile = "$filename.tmp";
    open $in , '<:encoding(UTF-8)', $filename or die "Error: Cannot open input file: $!\n";
    open $out, '>:encoding(UTF-8)', $tempfile or die "Error: Cannot create temporary file: $!\n";
}



##### PROCESS INPUT & WRITE OUTPUT: ##########################################################################################################################################################################################################

my $tmpline1;
my $tmpline2;
while (my $line = <$in>) {
    chomp $line;
    $tmpline1 = &process_lrc_line_but_it_may_just_be_a_txt_file($line);			# this is done in WhisperAIProcessing.pm:	$tmpline2 = &limit_repeats($tmpline1, $MAX_KARAOKE_WIDTH_MINUS_ONE - 4);  
    print $out "$tmpline1\n";
}



##### CLOSE OUTPUT FILE: #####################################################################################################################################################################################################################

if (!$read_from_stdin) {
    close $in  or die "Error: Cannot close input file: $!\n";
    close $out or die "Error: Cannot close temporary file: $!\n";

    move $tempfile, $filename or die "Error: Cannot overwrite original file: $!\n";
}






################################################################################################################################################################################################################################################
##### SUBROUTINES: #############################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

sub process_lrc_line_but_it_may_just_be_a_txt_file {
    my ($line) = @_;																			# get line
	if ($line =~ /^\s*$/ || $line =~ /^\s*#/) { return $line; }								    # Preserve blank / comment-ish lines exactly:
	for my $re (@LRC_patterns_to_delete) { $line =~ s/$re//g; }									# remove       LRC-specific b.s.
    if ($USE_WORDS_MODE) { $line = &whisper_ai_postprocess($line,$LEAVE_CENSORSHIP); }			# remove WhisperAI-specific b.s.
	return $line;																				# return line
}

sub dlrcpusage {
	no warnings 'utf8';
    print <<'USAGE';
    Usage: perl lrc-postprocessor.pl [options] <file>

    Options:
      -w, --WhisperAI, --words      Enable advanced processing mode
      -s, --simple                  Disable advanced processing; only remove one final period
      -l, --leave_censorship        Disable the uncensoring of censored words
      -h, --help, -h, ?, /?, help   Display this help message.

    👿👿👿👿👿 WARNING: This script modifies the file inline! Hope you have a backup! 👿👿👿👿👿

    Description:
      Processes downloaded LRC files inline
      Does not validate timestamps.
USAGE

    exit;
}


1;


