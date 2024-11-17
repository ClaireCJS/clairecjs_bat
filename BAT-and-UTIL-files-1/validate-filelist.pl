#perl


my $DEBUG = 0;		#set to >=1 for "file DOES exist" msgs
use strict;
use vars qw{$i $existYES $existNO $messages};
my $line="";
my $messages="";
my $i=0;
my $existYES=0;
my $existNO=0;
while ($line=<STDIN>) {
	if ($line =~ /^#EXTINF:/) { next; }
	if ($line =~ /^#EXTM3U/ ) { next; }
	$i++;
	chomp $line;
	#print ".";
	if (($i % 250)==0) { print ".   $i \n"; }
	if (-e $line) {
		$existYES++;
	} else {
		$messages .= "FILE DOES NOT EXIST: $line\n";
		$existNO++;
	}
}
print "\n\n$messages";
print "\nTOTAL FILES: $i   ($existYES EXIST, $existNO DO";
if ($existNO == 1) { print "ES"; }
print " NOT) \n";