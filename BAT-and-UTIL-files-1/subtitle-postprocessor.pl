#NOTE: We've snuck out-of-scope functionality into this script. 
#NOTE: Just a little bit so far, but:
#NOTE:       default, but optional, de-censoring of a bad words is done in addition to removing periods :)


#!/usr/bin/env perl                                                                                    # Specify the script interpreter
use strict;                                                                                            # Enforce strict variable declaration rules
use warnings;                                                                                          # Display warnings for potential errors
use File::Copy qw(move);                                                                               # Import move() for replacing files
use utf8;
binmode(STDOUT, ":utf8");
binmode(STDIN , ":utf8");
binmode(STDERR, ":utf8");

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Parse command-line arguments to determine the mode of execution.
# ——words or -w enables "words mode", which processes exceptions for abbreviations, ellipses, etc.
# Other options like ——help provide usage information.
# —————————————————————————————————————————————————————————————————————————————————————————————————————

my $leave_censorship = 0;
my $use_words_mode   = 0;                                                                              # Default: do not use words mode
my $do_test_suite    = 0;
my $filename;                                                                                          # Variable to hold the input file name
my $tmpLine;

foreach my $arg (@ARGV) {                                                                              # Iterate over command-line arguments
    if ($arg eq '--words' || $arg eq '-w') {                                                           # Check if ——words or -w is passed
        $use_words_mode = 1;                                                                           # Enable words mode if it was
    } elsif ($arg eq '-l' || $arg eq '--leave_censorship' ) {                                          # Check if ——words or -w is passed
        $leave_censorship = 1;                                                                         # Enable words mode if it was
    } elsif ($arg eq '-t' || $arg eq '--test' ) {                                          
		$do_test_suite=1
    } elsif ($arg =~ /^(\-\-?|\/?)he?l?p?$/i) {                                                        # Match common help flags
        print <<'USAGE';                                                                               # Print usage instructions and exit
Usage: perl remove_periods.pl [options] <file>
Options:
  --words, -w               Enable advanced mode with exceptions for titles, abbreviations, etc.
  --leave_censorship, -L    Disable the uncensoring of censored words
  --help, -h, ?, /?, help   Display this help message.
Description:
  Default mode:
    Removes exactly one period from the end of each line, no exceptions.
  Advanced mode (--words, -w):
    Preserves periods in common abbreviations (e.g., "Mr.", "Dr.") and ellipses ("...").
  The script modifies the file inline.
USAGE
        exit;                                                                                          # Exit after showing usage information
    } elsif (!$filename) {                                                                             # Treat the first non-flag argument as the file name
        $filename = $arg;                                                                              # Set the file name
    }
}

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Test Suite
# —————————————————————————————————————————————————————————————————————————————————————————————————————

if ($do_test_suite == 1) { 
	print &de_censor_original  ("f*ck") . "\n";
	print &de_censor_chatgpt_1 ("f*ck") . "\n";
	print &de_censor_production("f*ck") . "\n";
	print &de_censor_production("fuck") . "\n";
	print &de_censor_production("*uck") . "\n";
	print &de_censor_production("f*ck") . "\n";
	print &de_censor_production("fu*k") . "\n";
	print &de_censor_production("fuc*") . "\n";
	print &de_censor_production("**ck") . "\n";
	print &de_censor_production("*u*k") . "\n";
	print &de_censor_production("*uc*") . "\n";
	print &de_censor_production("f**k") . "\n";
	print &de_censor_production("f*c*") . "\n";
	print &de_censor_production("fu**") . "\n";
	print &de_censor_production("f***") . "\n";
	print &de_censor_production("*u**") . "\n";
	print &de_censor_production("**c*") . "\n";
	print &de_censor_production("***k") . "\n";

	print &de_censor_production("p*ss") . "\n";
	print &de_censor_production("piss") . "\n";
	print &de_censor_production("*iss") . "\n";
	print &de_censor_production("p*ss") . "\n";
	print &de_censor_production("pi*s") . "\n";
	print &de_censor_production("pis*") . "\n";
	print &de_censor_production("**ss") . "\n";
	print &de_censor_production("*i*s") . "\n";
	print &de_censor_production("*is*") . "\n";
	print &de_censor_production("p**s") . "\n";
	print &de_censor_production("p*s*") . "\n";
	print &de_censor_production("pi**") . "\n";
	print &de_censor_production("p***") . "\n";
	print &de_censor_production("*i**") . "\n";
	print &de_censor_production("**s*") . "\n";
	print &de_censor_production("***s") . "\n";

	die("Test suite complete");
}		


# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Validate the input file.
# —————————————————————————————————————————————————————————————————————————————————————————————————————

if (!$filename) {                                                                                      # Ensure a file name was provided
    die "Error: No file specified.\nUse --help for usage instructions.\n";                             # Exit with error if no file is specified
}
if (!-e $filename) {                                                                                   # Check if the file exists
    die "Error: File '$filename' does not exist.\n";                                                   # Exit with error if the file does not exist
}

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Execute the program logic based on the selected mode.
# If words mode is active, load an exception list and handle advanced cases.
# Otherwise, perform a simple end-of-line period removal.
# The modifications are written back to the file inline.
# —————————————————————————————————————————————————————————————————————————————————————————————————————

open my $in, '<:encoding(UTF-8)', $filename or die "Error: Cannot open '$filename': $!\n";             # Open the file for reading with UTF-8 encoding
my $tempfile = "$filename.tmp";                                                                        # Temporary file to write modifications
open my $out, '>:encoding(UTF-8)', $tempfile or die "Error: Cannot create temporary file: $!\n";       # Open the temporary file for writing with UTF-8 encoding

print $out "# Generated by Claire\n";

if ($use_words_mode) {                                                                                 # If words mode is enabled
    # Define a list of common exceptions where periods are preserved                                 
    my @exceptions = qw(                                                                             
        Mr Dr Jr Sr Ms Mrs Mx Prof St Fr etc vs v. e.g i.e viz Hon Gen Col Capt Adm Sen              
        Rev Gov Pres Lt Cmdr Sgt Pvt Maj Ave Blvd Rd Hwy Pk Pl Sq Ln Ct                              
        Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft    Vol Ch Sec Div Dep Dept                      
        U.S U.K U.N U.A.E E.U A.T.M I.M.F W.H.O N.A.S.A                                              
        Ph.D M.D B.A M.A D.D.S J.D D.V.M B.Sc M.B.A B.F.A M.F.A                                      
        A.D B.C BCE CE C.E B.P T.P R.C A.C a.m p.m A.M P.M                                           
        St. N.Y. L.A. D.C. Chi. S.F. B.K.                                                            
        approx esp fig min     std var coeff corr dep est lim val eq dif exp                         
        opp alt gen rel abs simp conv coeff asym diag geom alg trig calc                             
        vol chap pg sec ex exs     ref       fig     sup eqn prop cor sol prob                       
        adj adv     aux cl     conj det exclam intj n. nn np vb prn pron                             
    );
#      Mr Dr Jr Sr Ms Mrs Mx Prof St Fr etc vs v. e.g i.e viz Hon Gen Col Capt Adm Sen                 # Titles and general abbreviations
#      Rev Gov Pres Lt Cmdr Sgt Pvt Maj Ave Blvd Rd Hwy Pk Pl Sq Ln Ct                                 # Street, road, and location abbreviations
#      Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft No Vol Ch Sec Div Dep Dept                         # Corporate and geographic terms
#      Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft    Vol Ch Sec Div Dep Dept                       
#      U.S U.K U.N U.A.E E.U A.T.M I.M.F W.H.O N.A.S.A                                                 # Country and organizational abbreviations
#      Ph.D M.D B.A M.A D.D.S J.D D.V.M B.Sc M.B.A B.F.A M.F.A                                         # Academic and professional degrees
#      A.D B.C BCE CE C.E B.P T.P R.C A.C a.m p.m A.M P.M                                              # Historical and time-related terms
#      St. N.Y. L.A. D.C. Chi. S.F. B.K.                                                               # Common city/state abbreviations
#      approx esp fig min     std var coeff corr dep est lim val eq dif exp                            # Scientific and statistical abbreviations: removed some
#      opp alt gen rel abs simp conv coeff asym diag geom alg trig calc                                # Mathematical and geometric terms
#      vol chap pg sec ex exs     ref       fig     sup eqn prop cor sol prob                          # Book and academic citations: removed some
#      adj adv     aux cl     conj det exclam intj n. nn np vb prn pron                                # Grammatical and linguistic abbreviations: removed some
#      #approx esp fig min max std var coeff corr dep est lim val eq dif exp                           # Scientific and statistical abbreviations
#      #vol chap pg sec ex exs add ref trans fig app sup eqn prop cor sol prob                         # Book and academic citations
#      #adj adv art aux cl con conj det exclam intj n. nn np vb prn pron pro                           # Grammatical and linguistic abbreviations


    my $exceptions_regex = join '|', map { quotemeta } @exceptions;                                    # Build a regex from exceptions, escaping special characters

    # —————————————————————————————————————————————————————————————————————————————————————————————————
    # Words mode processing loop:
    # - Preserve ellipses ("...")
    # - Preserve periods in exceptions
    # - Remove other end-of-line periods
    # —————————————————————————————————————————————————————————————————————————————————————————————————

    while (<$in>) {                                                                                    # Read the file line by line
        chomp;                                                                                         # Remove the newline for safer processing
		if ($leave_censorship) {
			$tmpLine = $_;
		} else {
			$tmpLine = &whisper_ai_postprocess($_);
		}
        if ($tmpLine =~ /\.\.\.\s*$/) {                                                                # Check if line ends with ellipses ("...")
            print $out "$tmpLine\n";                                                                   # if so, print the line as-is to the output file
            next;                                                                                      # and then skip further processing for this line
        }																						 	   
        if ($tmpLine =~ /(\b(?:$exceptions_regex))\.\s*$/i) {                                          # Check if the line ends with a recognized exception ("Ms.")
            print $out "$tmpLine\n";                                                                   # if so, Print the line as-is to the output file
            next;                                                                                      # and skip further processing for this line
        }																						 	   
        $tmpLine =~ s/\.\s*$//;                                                                        # Remove a single trailing period (and spaces)
        print $out  "$tmpLine\n";                                                                      # Print the modified line to the output file
    }																							 	   
} else {                                                                                               # Default mode: blind period removal
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    # Simple mode processing loop:
    # - Remove exactly one period from the end of the line
    # - Does not check for ellipses or exceptions
    # —————————————————————————————————————————————————————————————————————————————————————————————————

    while (<$in>) {                                                                                    # Read the file line by line
        chomp;                                                                                         # Remove the newline for safer processing
        s/\.$//;                                                                                       # Remove exactly one trailing period
		if ($leave_censorship) {
			$tmpLine = $_;
		} else {
			$tmpLine = &whisper_ai_postprocess($_);
		}
        print $out "$tmpLine\n";                                                                       # Print the modified line to the output file
    }
}

close $in  or die "Error: Cannot close input file: "     . "$!\n";                                     # Close the input file
close $out or die "Error: Cannot close temporary file: " . "$!\n";                                     # Close the temporary file
move $tempfile, $filename or die "Error: Cannot overwrite original file: $!\n";                        # Replace the original file with the temporary file





sub de_censor_original {
	my $s=$_[0];

	#un-f**k:
	$s =~ s/\b(f)(\*)(\*)(\*)/$1uck/gi;	#f***
	$s =~ s/\b(\*)(u)(\*)(\*)/f$1ck/gi;	#*u**
	$s =~ s/\b(\*)(\*)(c)(\*)/fu$1k/gi;	#**c*
	$s =~ s/\b(\*)(\*)(\*)(k)/fuc$1/gi;	#***k

	$s =~ s/\b(\*)(\*)(c)(k)/fu$1$2/gi;	#**ck
	$s =~ s/\b(\*)(u)(\*)(k)/f$1c$2/gi;	#*u*k
	$s =~ s/\b(\*)(u)(c)(\*)/f$1$2k/gi;	#*uc*
	$s =~ s/\b(f)(\*)(\*)(k)/$1uc$2/gi;	#f**k
	$s =~ s/\b(f)(\*)(c)(\*)/$1u$2k/gi;	#f*c*
	$s =~ s/\b(f)(u)(\*)(\*)/$1$2ck/gi;	#fu**
	
	$s =~ s/\b(\*)(u)(c)(k)/f$1$2$3/gi;	#*uck
	$s =~ s/\b(f)(\*)(c)(k)/$1u$2$3/gi;	#f*ck
	$s =~ s/\b(f)(u)(\*)(k)/$1$2c$3/gi;	#fu*k
	$s =~ s/\b(f)(u)(c)(\*)/$1$2$3k/gi;	#fuc*
	
	return($s);
}	

sub de_censor_chatgpt_1 {
	my $s=$_[0];

	# List of 4-letter curse words
	my @four_letter_words = qw(fuck shit piss);

	# Iterate through each curse word
	for my $word (@four_letter_words) {
		my @chars = split //, $word; # Split the word into individual characters

		# Generate the substitution patterns for all possible masked combinations
		for my $i (0 .. 3) {
			for my $j ($i .. 3) {
				my @pattern = ('*', '*', '*', '*');
				$pattern[$i] = $chars[$i]; # Unmask the i-th character
				$pattern[$j] = $chars[$j] if $i != $j; # Optionally unmask the j-th character

				# Construct the regex pattern and replacement
				my $regex = "\\b" . join('', @pattern) . "\\b"; # Create masked word
				$regex =~ s/\*/\\w/g; # Replace * with \w to match any word character
				my $replacement = $word; # Replace with the original word

				# Perform the substitution
				$s =~ s/$regex/$replacement/gi;
			}
		}
	}
	return($s);
}

sub de_censor_production_approved {
    my $s = $_[0];

    # Handle specific patterns first to fully uncensor "f*ck"-like cases
    $s =~ s/(?:^|\b)(f)(\*)(c)(k)/$1u$3$4/gi;  # f*ck -> fuck
    $s =~ s/(?:^|\b)(f)(u)(\*)(k)/$1$2c$4/gi;  # fu*k -> fuck
    $s =~ s/(?:^|\b)(f)(u)(c)(\*)/$1$2$3k/gi;  # fuc* -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(c)(k)/f$2$3$4/gi;  # *uck -> fuck

    # General cases that unmask other letters
    $s =~ s/(?:^|\b)(f)(\*)(\*)(k)/$1uc$4/gi;  # f**k -> fuck
    $s =~ s/(?:^|\b)(f)(\*)(c)(\*)/$1u$3k/gi;  # f*c* -> fuck
    $s =~ s/(?:^|\b)(f)(u)(\*)(\*)/$1$2ck/gi;  # fu** -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(\*)(k)/f$2c$4/gi;  # *u*k -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(c)(\*)/f$2$3k/gi;  # *uc* -> fuck
    $s =~ s/(?:^|\b)(\*)(\*)(c)(k)/fu$3$4/gi;  # **ck -> fuck
	
    $s =~ s/(?:^|\b)(\*)(\*)(\*)(k)/fuc$4/gi;  # ***k -> fuck
    $s =~ s/(?:^|\b)(\*)(\*)(c)(\*)/fu$3k/gi;  # **c* -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(\*)(\*)/f$2ck/gi;  # *u** -> fuck
    $s =~ s/(?:^|\b)(f)(\*)(\*)(\*)/$1uck/gi;  # f*** -> fuck

    return $s;
}
sub de_censor_production_old1 {
    my $s = $_[0];

    # Handle specific patterns first to fully uncensor "f*ck"-like cases
    $s =~ s/(?:^|\b)(f)(\*)(c)(k)/$1u$3$4/gi;  # f*ck -> fuck
    $s =~ s/(?:^|\b)(f)(u)(\*)(k)/$1$2c$4/gi;  # fu*k -> fuck
    $s =~ s/(?:^|\b)(f)(u)(c)(\*)/$1$2$3k/gi;  # fuc* -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(c)(k)/f$2$3$4/gi;  # *uck -> fuck

    # General cases that unmask other letters
    $s =~ s/(?:^|\b)(f)(\*)(\*)(k)/$1uc$4/gi;  # f**k -> fuck
    $s =~ s/(?:^|\b)(f)(\*)(c)(\*)/$1u$3k/gi;  # f*c* -> fuck
    $s =~ s/(?:^|\b)(f)(u)(\*)(\*)/$1$2ck/gi;  # fu** -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(\*)(k)/f$2c$4/gi;  # *u*k -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(c)(\*)/f$2$3k/gi;  # *uc* -> fuck
    $s =~ s/(?:^|\b)(\*)(\*)(c)(k)/fu$3$4/gi;  # **ck -> fuck
	
    $s =~ s/(?:^|\b)(\*)(\*)(\*)(k)/fuc$4/gi;  # ***k -> fuck
    $s =~ s/(?:^|\b)(\*)(\*)(c)(\*)/fu$3k/gi;  # **c* -> fuck
    $s =~ s/(?:^|\b)(\*)(u)(\*)(\*)/f$2ck/gi;  # *u** -> fuck
    $s =~ s/(?:^|\b)(f)(\*)(\*)(\*)/$1uck/gi;  # f*** -> fuck

    return $s;
}

sub de_censor_production {
	my $s = $_[0];

	my @four_letter_curse_words = ('fuck', 'shit', 'cunt', 'piss', 'cock', 'crap', 'dick');				# Array of four-letter curse words
	
	foreach my $curse_word (@four_letter_curse_words) {							# Loop through each curse word
		my ($F, $U, $C, $K) = split(//, $curse_word);							# Assign variables for each character in the curse word
		$s =~ s/(?:^|\b)($F)(\*)(\*)(\*)/$1$U$C$K/gi; # f*** or s***
		$s =~ s/(?:^|\b)(\*)($U)(\*)(\*)/$F$2$C$K/gi; # *u** or *h**
		$s =~ s/(?:^|\b)(\*)(\*)($C)(\*)/$F$U$3$K/gi; # **c* or **i*
		$s =~ s/(?:^|\b)(\*)(\*)(\*)($K)/$F$U$C$4/gi; # ***k or ***t
		$s =~ s/(?:^|\b)(\*)(\*)($C)($K)/$F$U$3$4/gi; # **ck or **it
		$s =~ s/(?:^|\b)(\*)($U)(\*)($K)/$F$2$C$4/gi; # *u*k or *h*t
		$s =~ s/(?:^|\b)(\*)($U)($C)(\*)/$F$2$3$K/gi; # *uc* or *hi*
		$s =~ s/(?:^|\b)($F)(\*)(\*)($K)/$1$U$C$4/gi; # f**k or s**t
		$s =~ s/(?:^|\b)($F)(\*)($C)(\*)/$1$U$3$K/gi; # f*c* or s*i*
		$s =~ s/(?:^|\b)($F)($U)(\*)(\*)/$1$2$C$K/gi; # fu** or sh**
		$s =~ s/(?:^|\b)(\*)($U)($C)($K)/$F$2$3$4/gi; # *uck or *hit or *iss
		$s =~ s/(?:^|\b)($F)(\*)($C)($K)/$1$U$3$4/gi; # f*ck or s*it
		$s =~ s/(?:^|\b)($F)($U)(\*)($K)/$1$2$C$4/gi; # fu*k or sh*t
		$s =~ s/(?:^|\b)($F)($U)($C)(\*)/$1$2$3$K/gi; # fuc* or shi*
	}
	return $s;
}
sub de_censor {
	my $s = $_[0];
	return &de_censor_production($s);
}	


sub whisper_ai_postprocess {
	my $s=$_[0];
	
	################ HALLUCATIONS: ################ 
	$s =~ s/A little pause... *//gi;						#...These are common WhisperAI hallucinations.
	$s =~ s/And we are back\.*//gi;							#...These are common WhisperAI hallucinations.
	
	################# CENSORSHIP: ################# 
	$s = &de_censor($s);

	################ SPECIAL CHARS: ############### 
	$s =~ s/[â'`]/’/ig;										#apostrophes and misrepresentations thereof
	
	############# LYRIC WEBSITE JUNK: #############
	$s =~ s/You might also like//i;
	$s =~ s/^(.*[a-zA-Z])Embed\.?$/$1/i;

	return($s);
}

