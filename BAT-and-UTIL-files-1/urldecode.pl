#!perl

#use URI::Escape;
#uri_unescape($val);

my $line="";
my $original_line="";
while ($line=<STDIN>) {
	$original_line=$line;
	chomp $line;


	$line =~ s/\%([A-Fa-f0-9]{2})/pack('C', hex($1))/seg;

	print $line;
}