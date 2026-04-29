package WhisperAIProcessing;

use strict;
use warnings;
use Exporter 'import';
use FindBin;
use lib $FindBin::Bin;
use DeCensor;
use LimitRepeats;
use LyricsProcessing;
use CharacterEncodingFlaws;
use AbbreviatedWords;
our @EXPORT = qw(
	@hallucination_patterns
	whisper_ai_postprocess
	$MAX_KARAOKE_WIDTH
	$MAX_KARAOKE_WIDTH_MINUS_ONE
	$MAX_KARAOKE_WIDTH_MINUS_ONE_TIMES_2
);

our $MAX_KARAOKE_WIDTH                   = 25;								 # This system aims for a max width of 25
our $MAX_KARAOKE_WIDTH_MINUS_ONE         = $MAX_KARAOKE_WIDTH           - 1;  # used for formatting
our $MAX_KARAOKE_WIDTH_MINUS_ONE_TIMES_2 = $MAX_KARAOKE_WIDTH_MINUS_ONE * 2;  # used for formatting


our @hallucination_patterns = (			# WhisperAI silence hallucination patterns -- also add to c:\bat\delete-bad-AI-transcriptions.bat
    qr/A little pause..?.? */i,
	qr/And we are back\.*/i,
	qr/A?n?d? ?this is the second one/i,                        
	qr/A?n?d? ?this is the third one/i,                        
	qr/A?n?d? ?this is the fourth one/i,                         
	qr/A?n?d? ?this is the fifth one/i,                         
    qr/Ding, ding, bop ?/i,
    qr/I.m going to play a little bit of the first one, and then we.ll move on to the next one ?/i,
    qr/Thank you for watching/i,
    qr/Thanks for watching/i,
    qr/This is the first sentence/i,
	qr/This is the second sentence/i,                         
	qr/Ding, ding, bop/i,                                    
	qr/I.m going to play a little bit of the first one.*and then/i,
	qr/Thank you for watching[\.!]*/i,
	qr/Thanks for watching[\.!]*/i,
	qr/© BF-WATCH TV 2021/i,
);


sub whisper_ai_postprocess {
    my ($s, $LEAVE_CENSORSHIP, $REMOVE_PERIODS) = @_;
    $LEAVE_CENSORSHIP //= 0;
    $REMOVE_PERIODS   //= 0;
	
	################ CHAR-BASED CHARACTER FIXES: ############### 
	$s = &limit_repeats($s, $MAX_KARAOKE_WIDTH_MINUS_ONE - 4);								    # Fix lines like “Noooooooooooooooooooooooooooooooooooo” from being wider than our subtitle length
	$s = &fix_common_character_encoding_flaws($s);
	$s =~ s/^†/“/g;					                                                            #\__  WhisperAI keeps using the † symbol instead of “ for some reason
	$s =~ s/ †/ “/g;				                                                            #/
																							                            
	################ WORD-BASED PUNCTUATION FIXES: ################ 							                         
	$s =~ s/self \-righteous/self-righteous/g;													# 1)    proof of concept: fix hyphenated words that have an erroneous space before the hyphen
	$s =~ s/([a-z]) (\-)([a-z])/$1$2$3/ig;														# 2) generalized version: turn things like “double -dutch” back into “double-dutch”, since Whisper AI seems to do this
																							                            
	################ WORD-BASED WORD FIXES: ################ 								                            
	$s =~ s/our selves/ourselves/g;														        # common grammatical mistake
	$s =~ s/\bwont\b/won’t/gi;																                            
																							                            
	################ LINE-BASED FIXES: ################ 									                            
	if (!$LEAVE_CENSORSHIP) { $s =  &de_censor($s); }  											# remove censorship —— see —t option for testing the decensoring code
																							                            
	################ LINE-BASED FIXES ################
	for my $re (     @hallucination_patterns) { $s =~ s/$re//gi; }
	for my $re (@lyric_website_spam_patterns) { $s =~ s/$re//gi; }

	########## LINE-BASED PUNCTUATION FIXES: RELATED TO MY AI-MUSIC-TRANSCRIPTION SYSTEM: ########## 
	$s =~ s/^, *$//;																		    # remove leading comma like “, a line of text”
	if ($REMOVE_PERIODS == 1) {	$s = &remove_period_from_end_of_line_unless_abbreviation($s); }
	return($s);
}


1;

