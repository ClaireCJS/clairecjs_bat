package DeCensor;


use strict;
use warnings;
use Exporter 'import';

our @EXPORT = qw(
	de_censor
    de_censor_original
	de_censor_production
    decensorship_test_suite
	@four_letter_curse_words
	@five_letter_curse_words
);


our @four_letter_curse_words = qw(fuck        shit  cunt  cock  piss  twat  dick  crap );							# Array of four-letter curse words
our @five_letter_curse_words = qw(fucks bitch shits cunts cocks twats twats dicks craps prick pissy skank booty);	# Array of five-letter curse words

sub de_censor {
	my $s = $_[0];
	return &de_censor_production($s);
}	


sub de_censor_production {
	my $s = $_[0];


	# Create these arrays in order of commonality so that the more common ones match first:
																										           
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



################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

# —————————————————————————————————————————————————————————————————————————————————————————————————————
# De-Censorship Test Suite
# —————————————————————————————————————————————————————————————————————————————————————————————————————

sub decensorship_test_suite {
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




1;



