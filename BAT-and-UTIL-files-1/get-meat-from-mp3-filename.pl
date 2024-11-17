my $DEBUG=0;

	#####	
	#####	 This script's purpose is to take a filename of a song, and massage away anything that isn't the band name or title.
	#####	 This includes removing any common modifiers attached to songs, such as "(instrumental)" "(youtube-rip)", and anything
	#####	 else similar.
	#####	
	#####	 This script gets used in various workflows dealing with music.
	#####	
	#####	 Note that you can set environment varaiable PROCESSBEFOREHYPHENONLY to only process text before the first hyphen (erroneously called dash in some invocations)
	#####	
	#####	


	my $filename="@ARGV";


	if ($ENV{"PROCESSBEFOREDASHONLY"}   eq "1") { $filename =~ s/\-.*$//; }		#incorrect legacy invocation 
	if ($ENV{"PROCESSBEFOREHYPHENONLY"} eq "1") { $filename =~ s/\-.*$//; }		#  correct proper invocation


	#ALBUM-MODE STUFF: BEGIN:
		$filename =~ s/^[CSLBA-D0-9]* \- [12]\d{3} \- //;
		$filename =~ s/^[12]\d{3} \- //;
	#ALBUM-MODE STUFF: END

	#SOMETIMES GOOD, SOMETIMES BAD: BEGIN:
		#$filename =~ s/(\(live\))/ /i;
		#$filename =~ s/(\(demo\))/ /i;
		#$filename =~ s/(\([^\)]*Version\))/ /i;
		#$filename =~ s/(\([^\)]*Mix by [^\)]\))/ /i;
		#$filename =~ s/(\([^\)]*Mix\))/ /i;
	#SOMETIMES GOOD, SOMETIMES BAD: END


	#DO THIS FIRST:
	$filename =~ s/^\d?_?\d\d?_//;			#strip numbers at beginning


	#COMMON MUSIC-FILE MODIFIERS THAT ARE NOT PART OF THE "MEAT" OF THE NAME:
	$filename =~ s/\([FM]\)/ /gi;
	$filename =~ s/\(by [^\)]+\)/ /gi;
	$filename =~ s/\(youtube-rip\)/ /gi;
	$filename =~ s/\(vinyl-rip\)/ /gi;
	$filename =~ s/\(web-rip\)/ /gi;
	$filename =~ s/\([0-9\.\s]kHz\)/ /gi;
	$filename =~ s/\.\s*/.*/g;				
	$filename =~ s/\(Christmas\)/ /gi;
	$filename =~ s/\(phased\)/ /gi;
	&debug("[A1]");
	$filename =~ s/\(distorted\)/ /gi;
	$filename =~ s/\(denoised\)/ /gi;
	$filename =~ s/\(instrumental\)/ /gi;
	$filename =~    s/^d?_?\d\d_//gi;
	$filename =~ s/ \- d?_?\d\d_/ - /gi;
	$filename =~ s/\([0-9]+min\)/ /i;
	$filename =~ s/\([0-9]+min ver\)/ /i;
	$filename =~ s/\([0-9]+min[^\)]*v?e?r?s?i?o?n?\)/ /i;
	$filename =~ s/\([0-9]+m[0-9]+s\)/ /i;
	$filename =~ s/\([0-9]+m[0-9]+s ver\)/ /i;
	$filename =~ s/\([0-9]+m[0-9]+s[^\)]*v?e?r?s?i?o?n?\)/ /i;
	$filename =~ s/(\([LMH]Q\))/ /i;
	$filename =~ s/(\(mono[^\)]*\))/ /i;
	$filename =~ s/\([a-z][^\)]+ snd\)/ /i;
	$filename =~ s/(\(VBR\))/ /i;
	$filename =~ s/(\([^\)]*parody\))/ /i;
	&debug("[B1]");
	$filename =~ s/(\([^\)]* quality\))/ /i;
	$filename =~ s/(\(from [^\)]* soundtrack\))/ /i;
	$filename =~ s/(\(has.*pop!*\))/ /i;
	$filename =~ s/\([0-9]+kbps\)/ /i;
	$filename =~ s/(\([12][0-9][0-9][0-9]\))/ /i;
	$filename =~ s/ *\.mp3$/ /i;
	$filename =~ s/\(staticy\)/ /ig;
	$filename =~ s/\(vidcap\)/ /ig;
	$filename =~ s/\([0-9]*k?h?z? ?hissy ?s?o?u?n?d?\)/ /ig;
	$filename =~ s/\(from [^\)]* AVI\)/ /ig;
	$filename =~ s/ \- / /g;
	$filename =~ s/ & / and /g;
	$filename =~ s/witho?u?t? s?o?u?n?d? ?effects/ /;
	$filename =~ s/\.\*/ /g;							#regexes keep slippin' slippin'... into my search term

	#PROBATIONARY:
	&debug("[PRE-PROBATIONARY]");
	#No, I kinda want these, atually: $filename =~ s/\(opening theme\)/ /ig;
	#No, I kinda want these, atually: $filename =~ s/\(closing theme\)/ /ig;
	#No, I kinda want these, atually: $filename =~ s/ opening theme/ /ig;
	#No, I kinda want these, atually: $filename =~ s/ closing theme/ /ig;

	#2ND-TO-LAST:
	&debug("[PRE-2ND-TO-LAST]");
	$filename =~ s/ *\(from */ /;   #)))
	$filename =~ s/ full [0-9\.]+min vers?i?o?n?/ /;
	$filename =~ s/[\(\)]//g;

	#ALBUM-ART-ONLY STUFF - TODO?
	#commentedo out in 202410: $filename =~ s/closing theme/credits/;

	#DO LAST:
	&debug("[PRE-LAST]");
	$filename =~ s/  / /g;
	$filename =~ s/part [0-9]+ of [0-9]+//;
	$filename =~ s/ hissy / /;
	$filename =~ s/ mono / /;
	$filename =~ s/ buzzy / /;
	$filename =~ s/f?r?o?m? downloaded mkv/ /i;
	$filename =~ s/ mkv/ /;
	$filename =~ s/ vhs/ /;
	$filename =~ s/ mono / /;
	$filename =~ s/ mono$/ /;
	$filename =~ s/ ver / /;
	$filename =~ s/ vidcap / /;
	$filename =~ s/[0-9\.]+kHz/ /;
	$filename =~ s/ non\-?music / /;
	$filename =~ s/web-rip/ /;
	$filename =~ s/vinyl rip/ /;
	$filename =~ s/ mkv / /;
	$filename =~ s/' episode/' /;
	$filename =~ s/ [0-9]+kbps / /ig;


print $filename;


########################################################################
sub debug() {
	my $trace = $_[0];
	if ($DEBUG>0) { print "[DEBUG:$trace"."value=$filename]\n"; }
}
########################################################################
