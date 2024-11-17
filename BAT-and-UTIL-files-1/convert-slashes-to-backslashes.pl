use strict;
my $DEBUG=0;

my $line="";
while ($line = <STDIN>) {
	chomp $line;
	$line =~ s/\//\\/g;
	if ($DEBUG) { print "line is "; }
	print $line;
}