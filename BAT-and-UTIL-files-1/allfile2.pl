#!/usr/local/bin/perl


use utf8;										#20221102
use open qw( :std :encoding(UTF-8) );			#20221102
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');


#DEBUG: print "$ARGV[0]\n";
#DEBUG: print "$ARGV[1]\n";

open(NEWNAMES,"$ARGV[0]");           ##### 1st file, $tmp1, the   new    filenames
open(OLDNAMES,"$ARGV[1]");           ##### 2nd file, $tmp2, the original filenames

print "\necho * SWEEPING during BAT is " .    "\%SWEEPING\%" . "\n"  ;
print "\necho * SWEEPING during PL  is " . $ENV{"SWEEPING"}  . "\n\n";
my $IS_MODE_AUTO=0;
if ($ENV{"SWEEPING"}==1) { $IS_MODE_AUTO=1; }

print "call validate-environment-variable USERNAME\n";
print "SET TMPNAME=";
print "\%";
print "\@";
print "UNIQUE[\\]\n\n";         #don't be any more speicific than this,
                                #or you'll be copying instead of moving
                                #whenever you're on a different drive



#You should probably change "\\" to "c:\\windows\\temp"
#if you're only running one partition.
#Actually, c:\\windows isn't guarnateed for other OS ... $temp would be better.
#But \ seems to have worked for MANY years now .

my $RECURSIVE_MOVE=0;
if ($ENV{RECURSIVEMOVE}==1) { $RECURSIVE_MOVE=1; }

while (<NEWNAMES>) {
    # Get the new and old names from the input files and circumcize
    $currentNewName = $_;    $currentOldName = <OLDNAMES>;
    chop($currentNewName);   chop($currentOldName);

    # remove trailing spaces from filenames:
    $currentOldName =~ s/\s+$//;
    $currentNewName =~ s/\s+$//;

	if (!$RECURSIVE_MOVE) {
		$currentOldName =~ s/[\\\/]/ -- /g;
		$currentNewName =~ s/[\\\/]/ -- /g;
		$currentOldName =~ s/:/-/g;
		$currentNewName =~ s/:/-/g;
	}

    $currentOldName =~ s/\?/_/g;
    $currentNewName =~ s/\?/_/g;
    $currentOldName =~ s/\*/-/g;
    $currentNewName =~ s/\*/-/g;
    $currentOldName =~ s/\^/!/g;
    $currentNewName =~ s/\^/!/g;
    $currentOldName =~ s/\%[^\%]/%%/g;
    $currentNewName =~ s/\%[^\%]/%%/g;
    #$currentOldName =~ s/\[/(/g;
    #$currentNewName =~ s/\[/(/g;
    #$currentOldName =~ s/\]/)/g;
    #$currentNewName =~ s/\]/)/g;
    $currentOldName =~ s/\|/!/g;
    $currentNewName =~ s/\|/!/g;
    $currentOldName =~ s/"/'/g;
    $currentNewName =~ s/"/'/g;
    $currentOldName =~ s/</(/g;
    $currentNewName =~ s/</(/g;
    $currentOldName =~ s/>/)/g;
    $currentNewName =~ s/>/)/g;
    $currentNewName =~ s/\%/Percent/g;	#hmm -- another carolyn thing
    $currentNewName =~ s/\t/ /g;	    #hmm -- another carolyn thing
	# am I missing anything else?

    # Keep track of whether the filename is actually different...
    $differentFlag = 0;
     if ($currentNewName ne $currentOldName) { $differentFlag = 1; }

    # Issue a re-name if the filename is actually different
    if ($differentFlag == 1) {
        # This may seem strange, but if all you are changing in a file
        # is the case, rename wont always work. So it's best to rename
        # the file to a temp filename, then rename that to what you really
        # want.  OS stupidity...

	##### OHOH ... It would be awesome to convert currentOldName into the
	##### *SHORT* filename, this would allow to rename files a bit larger than
	##### we could before (due to 255 command line limit) .. though the destination
	##### name has to be full, so our destination filename must
	##### still be under 255 - len("move %TEMPFILENAME ") .. this would at least
	##### allow us to manipulate files that are between that number and 255
	##### characters in length......

	# Must deal with the fact that % is a special character at commandline,
	# even though it can be in a filename...
        $currentOldName =~ s/%/%%/g;
		$currentNewName =~ s/%//g;
  
		#rint "set TMPNAME=\\allfiles-\%_DATETIME.\%KNOWN_NAME\%.\%_PID.\%\@NAME[\%\@UNIQUE[\\]]\n";
		#20160922:
		print "set TMPNAME=allfiles-\%_DATETIME.\%KNOWN_NAME\%.\%_PID.\%\@NAME[\%\@UNIQUE[\\]]\n";
		#20221119 adding unicode support and running into the strangest bug where you can't quote filenames in environment variables
		#         in a way that lets you successfully check their existence, IF they have a unicode-quote in them. Further testing
		#         revealed these filename-environment-variables only behave correctly if quotes surround the DEFINING of the variable,
		#         a behavior we've not seen in 30+ yrs of dealing with this
		#NON-UNICODE:
		print "set OLDNAME=$currentOldName\n";
		print "set NEWNAME=$currentNewName\n";
		#ON SECOND THOUGHT! THIS FIXED THINGS IN INTERNAL TESTING BUT BROKE OTHER THINGS SO FUCK THIS. FUCK UNICODE QUOTES!
		#UNICODE:
		#rint "set OLDNAME=\"$currentOldName\"\n";
		#print "set NEWNAME=\"$currentNewName\"\n";
        print "            if exist \"\%NEWNAME\%\" .and. \"\%NEWNAME\%\" ne \"\%OLDNAME\%\" (echo %ANSI_COLOR_WARNING%WARNING! NEWNAME OF %BLINK_ON%%NEWNAME%%BLINK_OFF% ALREADY EXISTS! CHOOSE NEW NAME! %+ beep %+ beep %+ ";
		#no longer doing this with advent of windows terminal: print "window maximize %+ "
		print "eset NEWNAME %+ pause)\n";
        print "            if exist \"\%OLDNAME\%\" .and. not exist \"\%NEWNAME\%\" move /r /g "." \"\%OLDNAME\%\" \"\%TMPNAME\"\n";
        print "            if                             not exist \"\%NEWNAME\%\" move /r /g ". "  \%TMPNAME\%   \"\%NEWNAME\%\"\n";

        print "\n";
    }
}

close(NEWNAMES); 
close(OLDNAMES);    



