#!perl
my %SEEN=();
while ($line=<STDIN>) {
	if ($SEEN{$line} eq "") {
		print $line;
		$SEEN{$line}=1;		
	}
}