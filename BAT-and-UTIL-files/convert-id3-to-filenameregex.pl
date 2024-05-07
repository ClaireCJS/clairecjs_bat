use strict;
my $DEBUG=0;

my $line="";
while ($line = <STDIN>) {
	chomp $line;


	#### The magic happens here:
	$line =~ s/ - /.*/g;
	$line =~ s/\s*--\s*/.*/g;
	$line =~ s/\?/.*/g;	#they are usually _ in a filename, but if i put it ina  tag and not a filename, searching would make it fail, so let's not search for an _, let's just search for nothing if ther eis a ?
	$line =~ s/\s*\/\s*/.*/g;
	####

	#### The kludges happen here:
	$line =~ s/^[\-\s]+//;			#the cut point in the audioscrobbler logfile isn't always the smae ... sometimes we get a "- " at the beginning .. so we need to remove that  or the grep we do with that in the future will fail
	####

	#### Also, for example, "The Bangles" really is "Bangles, The".
	#### We should just remove "The".
	$line =~ s/^The //i;
	####
	
	#### Other good ideas to do while we're here:
	$line =~ s/^\s*//;			#also remove leading  spaces...seems like a harmless side-effect
	$line =~ s/\s*$//;			#also remove trailing spaces...seems like a harmless side-effect
	if ($DEBUG) { print "line is "; }
	print $line;
}