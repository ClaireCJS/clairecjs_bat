
my %FILELIST=();
while ($line=<STDIN>) {
	chomp($line);

	########### 9/12/2001   8:44a     70,361,088  Liquid Television - Running Man
	$line =~ /(..).(..).(....)..(..).(..)(.).................(.*)/;
	$MM   = $1;
	$DD   = $2;
	$YYYY = $3;
	$HH   = $4;
	$min  = $5;
	$M    = $6;
	$name = $7;
	if (($M =~ /p/i) && ($HH < 12)) { $HH += $12 }
	$datestamp = $YYYY . $MM . $DD . $HH . $min;
	$hashstamp = $datestamp . $name;

	#print "YYYY=$YYYY,MM=$MM,DD=$DD,HH=$HH,min=$min\n";#DEBUG
	#print "Adding: stamp=$hashstamp, data=$line\n\n\n";#DEBUG
	$FILELIST{$hashstamp} = $line;
}

my @keys = sort keys %FILELIST;
foreach $hashstamp (@keys) {
	print $FILELIST{$hashstamp} . "\n";
}
