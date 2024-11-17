use utf8;
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');

my $NON_UNICODE_FIXES=1;											#we do some non-unicode stuff too, and in the futue, might want to turn that off

while ($line=<>) {
	chomp $line; $original_line=$line;

	$line          =~ /^(.*)(\.[^\.]+)$/;						    #get base filename and extension
	$base          = $1;											#get base filename and extension
	$ext_with_dot  = $2;											#get base filename and extension
	#DEBUG: print "* line is $line\n\t-base is $base\n\t-ext_with_dot is $ext_with_dot\n";



	$line =~ s/:/- /g;		#unicode colon
	$line =~ s/：/- /g;		#ascii   colon
	$line =~ s/｜/-/g;		#unicode pipe
	$line =~ s/\|/-/g;	    #ascii   pipe




	if ($original_line eq $line) { $has_unicode_changes=0; } 
	else                         { $has_unicode_changes=1; }
	if ($NON_UNICODE_FIXES) {										##### The rest of these changes only happen if $NON_UNICODE_FIXES
		$line =~ s/  / /g;
		$line =~ s/ \- \- / - /g;
	}



	if ($has_unicode_changes==0) { 
		print "REM \"$original_line\" has no unicode characters\n"; 
	} else {
		print "mv \"$original_line\" \"$line\"\n"; 
	}
}