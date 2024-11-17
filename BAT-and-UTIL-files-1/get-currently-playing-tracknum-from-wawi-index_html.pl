my $DEBUG=0;






my @STDIN = <STDIN>;
my $track;
foreach my $line (@STDIN) {
	chomp  $line;
	print_if_debug($line . "\n");
	if    ($line =~    /Playing track ([0-9]+) /i) { $track = $1; }
	elsif ($line =~  /Paused in track ([0-9]+) /i) { $track = $1; }
	elsif ($line =~ /Stopped at track ([0-9]+) /i) { $track = $1; }
}
print $track;







sub print_if_debug { if ($DEBUG>0) { print $_[0]; } }
