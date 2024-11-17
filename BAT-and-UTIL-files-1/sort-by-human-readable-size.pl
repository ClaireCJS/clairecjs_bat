#!perl


my @INPUT=<STDIN>;
my %INPUT=();			#hash table: key=size, value=line from input

foreach my $line (@INPUT) {
	chomp $line;

	($size,$rest)=split(/\t/,$line);

	    $convertedSize = $size;
	if ($convertedSize =~ /K$/i) { $multiplier=1024**1; }	#determine multiplier
	if ($convertedSize =~ /M$/i) { $multiplier=1024**2; }	
	if ($convertedSize =~ /G$/i) { $multiplier=1024**3; }
	if ($convertedSize =~ /T$/i) { $multiplier=1024**4; }	
	    $convertedSize =~ s/^([0-9]+).*$/$1/;				#get just the number
	    $convertedSize *= $multiplier;

	$INPUT{$convertedSize} .= $line . "\n";		#prevent collisions by appending (some may be same size like "450M", don't want one to disappear)

	#DEBUG: 	print "Size=".sprintf("%-15s",$size)."\tmultiplier=".sprintf("%-15s",$multiplier)."  \tconvertedSize=".sprintf("%-20s",$convertedSize)."  \trest=$rest\n";
}


foreach $key (sort {$a <=> $b} keys %INPUT) { print $INPUT{$key}; }
