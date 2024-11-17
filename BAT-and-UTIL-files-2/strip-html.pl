use HTML::Strip;
 
my @input=<STDIN>;

my $hs = HTML::Strip->new();

foreach my $line (@input) {
	my $clean_text = $hs->parse( $line );
	$hs->eof;
	print $clean_text;
}

