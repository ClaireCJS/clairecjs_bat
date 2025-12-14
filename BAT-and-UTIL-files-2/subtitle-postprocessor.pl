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

################################################################################################################################################################################################################################################

################################## CONFIG: SUIBTITLE-SPECIFIC CONFIG: ################################## 

my $LEAVE_CENSORSHIP                    =  0;								 # Set to 0 to de-censor things, set to 1 to leave things censored
my $REMOVE_PERIODS                      =  1;                                # Remove a single trailing period (and spaces) including our “invisible periods” (that aren’t really invisible) which we deliberately place into our lyrics to force WhisperAI’s “--sentence” option to correctly process line breaks in a way that makes semantic sense
my $USE_WORDS_MODE                      =  1;                                # Checks for words that end in a period before removing periods from the end of each line
my $MAX_KARAOKE_WIDTH_MINUS_ONE         = 24;								 # This system aims for a max width of 25
my $MAX_KARAOKE_WIDTH_MINUS_ONE_TIMES_2 = $MAX_KARAOKE_WIDTH_MINUS_ONE * 2;  # used for formatting
my @hallucination_patterns              = (								     # WhisperAI silence hallucination
		qr/A little pause..?.? */i,
		qr/And we are back\.*/i,
		qr/Ding, ding, bop ?/i,
		qr/I.m going to play a little bit of the first one, and then we.ll move on to the next one ?/i,
		qr/This is the first sentence/i,                         
		qr/And this is the second one/i,                         # WhisperAI silence hallucination
		qr/Ding, ding, bop/i,                                    # WhisperAI silence hallucination
		qr/I.m going to play a little bit of the first one.*and then/i,
		qr/Thank you for watching/i,
		#### NOTE: Add new patterns to lyric-postprocessor.pl & delete-bad-AI-transcriptions.bat
);




																		   
################################## CONFIG: LIST OF ABBREVIATIONS: ################################## 
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
my $exceptions_regex = join '|', map { quotemeta } @exceptions;                                        # Build a regex from exceptions, escaping special characters
#   Mr Dr Jr Sr Ms Mrs Mx Prof St Fr etc vs v. e.g i.e viz Hon Gen Col Capt Adm Sen                    # Titles and general abbreviations
#   Rev Gov Pres Lt Cmdr Sgt Pvt Maj Ave Blvd Rd Hwy Pk Pl Sq Ln Ct                                    # Street, road, and location abbreviations
#   Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft No Vol Ch Sec Div Dep Dept                            # Corporate and geographic terms
#   Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft    Vol Ch Sec Div Dep Dept                       
#   U.S U.K U.N U.A.E E.U A.T.M I.M.F W.H.O N.A.S.A                                                    # Country and organizational abbreviations
#   Ph.D M.D B.A M.A D.D.S J.D D.V.M B.Sc M.B.A B.F.A M.F.A                                            # Academic and professional degrees
#   A.D B.C BCE CE C.E B.P T.P R.C A.C a.m p.m A.M P.M                                                 # Historical and time-related terms
#   St. N.Y. L.A. D.C. Chi. S.F. B.K.                                                                  # Common city/state abbreviations
#   approx esp fig min     std var coeff corr dep est lim val eq dif exp                               # Scientific and statistical abbreviations: removed some
#   opp alt gen rel abs simp conv coeff asym diag geom alg trig calc                                   # Mathematical and geometric terms
#   vol chap pg sec ex exs     ref       fig     sup eqn prop cor sol prob                             # Book and academic citations: removed some
#   adj adv     aux cl     conj det exclam intj n. nn np vb prn pron                                   # Grammatical and linguistic abbreviations: removed some
#   #approx esp fig min max std var coeff corr dep est lim val eq dif exp                              # Scientific and statistical abbreviations
#   #vol chap pg sec ex exs add ref trans fig app sup eqn prop cor sol prob                            # Book and academic citations
#   #adj adv art aux cl con conj det exclam intj n. nn np vb prn pron pro                              # Grammatical and linguistic abbreviations

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################



###### SET INITIAL FLAGS: ######################################################################################################################################################################################################################

my $do_test_suite    = 0;
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

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# Test-suite-only mode
# —————————————————————————————————————————————————————————————————————————————————————————————————————

if ($do_test_suite) {
	&do_test_suite;
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

print $out                                "\n";
print $out "# Generated by Claire"      . "\n";
print $out "# Sawyer’s WhisperAI-based" . "\n";
print $out "# transcription system."    . "\n";
print $out "# Kill yourself, Trumpers." . "\n";
print $out                                "\n";


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
		$tmpLine = &whisper_ai_postprocess($_);
        print $out  "$tmpLine\n";                                                                      # Print the modified line to the output file
    }																							 	   
} else {                                                                                               # Default mode: blind period removal
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    # Simple mode processing loop:
    # - Remove exactly one period from the end of the line and does nothign else
    # —————————————————————————————————————————————————————————————————————————————————————————————————
    foreach $_ (@fixed) {																			   # Read the file line by line
        chomp;                                                                                         # Remove the newline for safer processing
		#maybe don’t do this anymore! $tmpLine = &whisper_ai_postprocess($_);                          # don’t do our special WhisperAI-specific processing!
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



sub de_censor_f_suggested {
	my @five_letter_curses = qw(bitch bastd prick sluts dicks pissy twats craps
				fucks freak screw skank nutsy jerks wanks dumbs
				bimbo booty slutty dafto dingy goofy
				);

	my $s = shift;
	my @words = @five_letter_curses;
	foreach my $w (@words) {
		my @chars = split //, $w;
		my $masked = $chars[0] . '*' x (@chars - 2) . $chars[-1];
		$s =~ s/\b\Q$w\E\b/$masked/gi;
	}
	return $s;
}
sub de_censor_production {
	my $s = $_[0];

	# Create these arrays in order of commonality so that the more common ones match first:
	my @four_letter_curse_words = qw(fuck        shit  cunt  cock  piss  twat  dick  crap );							# Array of four-letter curse words
	my @five_letter_curse_words = qw(fucks bitch shits cunts cocks twats twats dicks craps prick pissy skank booty);	# Array of five-letter curse words
		
																								           
	foreach my $curse_word (@five_letter_curse_words) {											            # Loop through each curse word
		my ($B, $I, $T, $C, $H) = split(//, $curse_word);											        # 27 cases
		$s =~ s/(?:^|\b)(\*)($I)($T)($C)($H)/$B$2$3$4$5/gi; # *itch
		$s =~ s/(?:^|\b)($B)(\*)($T)($C)($H)/$1$I$3$4$5/gi; # b*tch
		$s =~ s/(?:^|\b)($B)($I)(\*)($C)($H)/$1$2$T$4$5/gi; # bi*ch
		$s =~ s/(?:^|\b)($B)($I)($T)(\*)($H)/$1$2$3$C$5/gi; # bit*h
		$s =~ s/(?:^|\b)($B)($I)($T)($C)(\*)/$1$2$3$4$H/gi; # bitc*

		$s =~ s/(?:^|\b)(\*)(\*)($T)($C)($H)/$B$I$3$4$5/gi; # **tch
		$s =~ s/(?:^|\b)(\*)($I)(\*)($C)($H)/$B$2$T$4$5/gi; # *i*ch
		$s =~ s/(?:^|\b)(\*)($I)($T)(\*)($H)/$B$2$3$C$5/gi; # *it*h
		$s =~ s/(?:^|\b)(\*)($I)($T)($C)(\*)/$B$2$3$4$H/gi; # *itc*
		$s =~ s/(?:^|\b)($B)(\*)(\*)($C)($H)/$1$I$T$4$5/gi; # b**ch
		$s =~ s/(?:^|\b)($B)(\*)($T)(\*)($H)/$1$I$3$C$5/gi; # b*t*h
		$s =~ s/(?:^|\b)($B)(\*)($T)($C)(\*)/$1$I$3$4$H/gi; # b*tc*
		$s =~ s/(?:^|\b)($B)($I)(\*)(\*)($H)/$1$2$T$C$5/gi; # bi**h
		$s =~ s/(?:^|\b)($B)($I)(\*)($C)(\*)/$1$2$T$4$H/gi; # bi*c*
		$s =~ s/(?:^|\b)($B)($I)($T)(\*)(\*)/$1$2$3$C$H/gi; # bit**

		$s =~ s/(?:^|\b)(\*)(\*)(\*)($C)($H)/$B$I$T$4$5/gi; # ***ch
		$s =~ s/(?:^|\b)(\*)(\*)($T)(\*)($H)/$B$I$3$C$5/gi; # **t*h
		$s =~ s/(?:^|\b)(\*)(\*)($T)($C)(\*)/$B$I$3$4$H/gi; # **tc*
		$s =~ s/(?:^|\b)($B)(\*)(\*)(\*)($H)/$1$I$T$C$5/gi; # b***h
		$s =~ s/(?:^|\b)($B)(\*)(\*)($C)(\*)/$1$I$T$4$H/gi; # b**c*
		$s =~ s/(?:^|\b)($B)(\*)($T)(\*)(\*)/$1$I$3$C$H/gi; # b*t**
		$s =~ s/(?:^|\b)($B)($I)(\*)(\*)(\*)/$1$2$T$C$H/gi; # bi***

		$s =~ s/(?:^|\b)(\*)(\*)(\*)(\*)($H)/$B$I$T$C$5/gi; # ****h
		$s =~ s/(?:^|\b)(\*)(\*)(\*)($C)(\*)/$B$I$T$4$H/gi; # ***c*
		$s =~ s/(?:^|\b)(\*)(\*)($T)(\*)(\*)/$B$I$3$C$H/gi; # **t**
		$s =~ s/(?:^|\b)(\*)($I)(\*)(\*)(\*)/$B$2$T$C$H/gi; # *i***
		$s =~ s/(?:^|\b)($B)(\*)(\*)(\*)(\*)/$1$I$T$C$H/gi; # b****																	   
	}
	foreach my $curse_word (@four_letter_curse_words) {											            # Loop through each curse word
		my ($F, $U, $C, $K) = split(//, $curse_word);											            # 14 cases
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
	if ($LEAVE_CENSORSHIP == 1) {
		return $s;
	} else {
		return &de_censor_production($s);
	}
}	


sub whisper_ai_postprocess {
	my $s=$_[0];
	
	################ CHAR-BASED CHARACTER FIXES: ############### 
	$s = &limit_repeats($s, $MAX_KARAOKE_WIDTH_MINUS_ONE - 4);								                             # Fix lines like “Noooooooooooooooooooooooooooooooooooo” from being wider than our subtitle length
	$s =~ s/\-\-([^>])/—$1/g;																	                         # fix “--” which is an archaic way of representing “—” ... Although this really should be turned into “——” if we are in a monospaced situation
	$s =~ s/[â′'`]/’/ig;																		                         # not-smart apostrophes and misrepresentations thereof
	$s =~ s/!“/!”/g;																			                         # copied from lyric-postprocessor: kludge bug fix
	$s =~ s/„/”/g;																				                         # copied from lyric-postprocessor: this is how Germans OPEN quotes („like this”), and we’re not German, so we convert „ to “
																							                            
	################ CHAR-BASED CHARACTER FIXES: COMMAND-LINE COMPATIBILITY ###############		                         # these aren’t needed because nothing in our subtitles ever reaches the command line!
	#BAD IDEA HERE: #s =~ s/"/'/g;																                         # change quotes to apostrophes so these can be used as a quoted command line argument ... makes no sense actually, this isn’t going to command line anymore
	#BAD IDEA HERE: $s =~ s/</⧼/g;																                         # redirection characters should not reach our command-line, which is what our lyrics mode is used for
	#BAD IDEA HERE: $s =~ s/"/'/g;																                         # change quotes to apostrophes so these can be used as a quoted command line argument
	#BAD IDEA HERE: $s =~ s/>/⧽/g;																                         # redirection characters should not reach our command-line, which is what our lyrics mode is used for
	#BAD IDEA HERE: s =~ s/\|/│/g;																                         # redirection characters should not reach our command-line, which is what our lyrics mode is used for
																							                            
	################ WORD-BASED PUNCTUATION FIXES: ################ 							                         
	$s =~ s/self \-righteous/self-righteous/g;													                         # 1)    proof of concept: fix hyphenated words that have an erroneous space before the hyphen
	$s =~ s/([a-z]) (\-)([a-z])/$1$2$3/ig;														                         # 2) generalized version: turn things like “double -dutch” back into “double-dutch”, since Whisper AI seems to do this
																							                            
	################ WORD-BASED WORD FIXES: ################ 								                            
	$s =~ s/our selves/ourselves/g;														                                 # common grammatical mistake
	$s =~ s/\bwont\b/won’t/gi;																                            
																							                            
	################ LINE-BASED FIXES: ################ 									                            
	$s =  &de_censor($s);																		                         # remove censorshi —— see —t option for testing the decensoring code
																							                            
	################ LINE-BASED FIXES: WHISPER-AI HALLUCATIONS ################
	for my $re (@hallucination_patterns) { $s =~ s/$re//g; }

	
	################ LINE-BASED FIXES: LYRIC WEBSITE SPAM: ################						# If our code was more honest, this would be in a separate function as it’s not *directly* related to WhisperAI postprocessing, and more of an artifact of downloading lyrics from websites with autodownloaders like “LyricsGenius.exe”
	$s =~ s/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used//i;
	$s =~ s/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+//i;
	$s =~ s/\*? ?Downloaded from: http:\/\/[^ ]+//i;
	$s =~ s/Get tickets as low as \$[\d\.]+//i;
	$s =~ s/Album tracklist with lyrics//;
	$s =~ s/^(.*[a-zA-Z])Embed\.?$/$1/i;														# common junk found in downloaded lyrics
	$s =~ s/You might also like//i;																# common junk found in downloaded lyrics

	########## LINE-BASED PUNCTUATION FIXES: RELATED TO MY AI-MUSIC-TRANSCRIPTION SYSTEM: ########## 
	$s =~ s/^, *$//;																		    # remove leading comma like “, a line of text”
	if ($REMOVE_PERIODS == 1) {	
			if    ( $s =~ /\.\.\.\s*$/) { $s =~ s/\.\.\.\.$/.../; }                             # Check if line ends with ellipses (“..."), if so, don’t use our period-removal code, but DO change a line ending in “....” to “...”
			elsif ( $s =~ /(\b(?:$exceptions_regex))\.\s*$/i) { }                               # Otherwise, check if the line ends with a recognized exception (“Ms.”)
			else  { $s =~ s/\.\s*$//;}															# Remove a single trailing period (and spaces) including our “invisible periods”
	}                                                
		  
	return($s);
}


sub limit_repeats {
    my ($s, $max) = @_;
    my $result = '';
    my $last_char = '';
    my $count = 0;

    foreach my $c (split //, $s) {
        if ($c eq $last_char) {
            $count++;
        } else {
            $last_char = $c;
            $count = 1;
        }
        $result .= $c if $count <= $max;
    }

    return $result;
}


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

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# De-Censorship Test Suite
# —————————————————————————————————————————————————————————————————————————————————————————————————————

sub do_test_suite {
	print " f*ck ➜  " . &de_censor_production("f*ck")  . "\n";
	print " fuck ➜  " . &de_censor_production("fuck")  . "\n";
	print " *uck ➜  " . &de_censor_production("*uck")  . "\n";
	print " f*ck ➜  " . &de_censor_production("f*ck")  . "\n";
	print " fu*k ➜  " . &de_censor_production("fu*k")  . "\n";
	print " fuc* ➜  " . &de_censor_production("fuc*")  . "\n";
	print " **ck ➜  " . &de_censor_production("**ck")  . "\n";
	print " *u*k ➜  " . &de_censor_production("*u*k")  . "\n";
	print " *uc* ➜  " . &de_censor_production("*uc*")  . "\n";
	print " f**k ➜  " . &de_censor_production("f**k")  . "\n";
	print " f*c* ➜  " . &de_censor_production("f*c*")  . "\n";
	print " fu** ➜  " . &de_censor_production("fu**")  . "\n";
	print " f*** ➜  " . &de_censor_production("f***")  . "\n";
	print " *u** ➜  " . &de_censor_production("*u**")  . "\n";
	print " **c* ➜  " . &de_censor_production("**c*")  . "\n";
	print " ***k ➜  " . &de_censor_production("***k")  . "\n";
		        	    								   
	print " p*ss ➜  " . &de_censor_production("p*ss")  . "\n";
	print " piss ➜  " . &de_censor_production("piss")  . "\n";
	print " *iss ➜  " . &de_censor_production("*iss")  . "\n";
	print " p*ss ➜  " . &de_censor_production("p*ss")  . "\n";
	print " pi*s ➜  " . &de_censor_production("pi*s")  . "\n";
	print " pis* ➜  " . &de_censor_production("pis*")  . "\n";
	print " **ss ➜  " . &de_censor_production("**ss")  . "\n";
	print " *i*s ➜  " . &de_censor_production("*i*s")  . "\n";
	print " *is* ➜  " . &de_censor_production("*is*")  . "\n";
	print " p**s ➜  " . &de_censor_production("p**s")  . "\n";
	print " p*s* ➜  " . &de_censor_production("p*s*")  . "\n";
	print " pi** ➜  " . &de_censor_production("pi**")  . "\n";
	print " p*** ➜  " . &de_censor_production("p***")  . "\n";
	print " *i** ➜  " . &de_censor_production("*i**")  . "\n";
	print " **s* ➜  " . &de_censor_production("**s*")  . "\n";
	print " ***s ➜  " . &de_censor_production("***s")  . "\n";
				    
	print "*itch ➜  " . &de_censor_production("*itch") . "\n";
	print "b*tch ➜  " . &de_censor_production("b*tch") . "\n";
	print "bi*ch ➜  " . &de_censor_production("bi*ch") . "\n";
	print "bit*h ➜  " . &de_censor_production("bit*h") . "\n";
	print "bitc* ➜  " . &de_censor_production("bitc*") . "\n";
	print "**tch ➜  " . &de_censor_production("**tch") . "\n";
	print "*i*ch ➜  " . &de_censor_production("*i*ch") . "\n";
	print "*it*h ➜  " . &de_censor_production("*it*h") . "\n";
	print "*itc* ➜  " . &de_censor_production("*itc*") . "\n";
	print "b**ch ➜  " . &de_censor_production("b**ch") . "\n";
	print "b*t*h ➜  " . &de_censor_production("b*t*h") . "\n";
	print "b*tc* ➜  " . &de_censor_production("b*tc*") . "\n";
	print "bi**h ➜  " . &de_censor_production("bi**h") . "\n";
	print "bi*c* ➜  " . &de_censor_production("bi*c*") . "\n";
	print "bit** ➜  " . &de_censor_production("bit**") . "\n";
	print "***ch ➜  " . &de_censor_production("***ch") . "\n";
	print "**t*h ➜  " . &de_censor_production("**t*h") . "\n";
	print "**tc* ➜  " . &de_censor_production("**tc*") . "\n";
	print "b***h ➜  " . &de_censor_production("b***h") . "\n";
	print "b**c* ➜  " . &de_censor_production("b**c*") . "\n";
	print "b*t** ➜  " . &de_censor_production("b*t**") . "\n";
	print "bi*** ➜  " . &de_censor_production("bi***") . "\n";
	print "****h ➜  " . &de_censor_production("****h") . "\n";
	print "***c* ➜  " . &de_censor_production("***c*") . "\n";
	print "**t** ➜  " . &de_censor_production("**t**") . "\n";
	print "*i*** ➜  " . &de_censor_production("*i***") . "\n";
	print "b**** ➜  " . &de_censor_production("b****") . "\n";

	print "w*tch ➜  " . &de_censor_production("w*tch") . "\n";
								  
	die("*** Test suite complete ***");	 
}								 

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

