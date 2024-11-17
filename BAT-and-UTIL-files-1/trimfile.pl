my $quote=0;
while ($line=<STDIN>) {
	if ($line =~ /\"$/) { $quote=1; }
	else                { $quote=0; }
	$line =~ s/(^.*[\\\/])[^\\\/]+(\"*)$/$1/g; 
	if ($quote) { $line .= "\"";}
	print $line . "\n";
}
