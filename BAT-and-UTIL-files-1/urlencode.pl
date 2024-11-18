#!perl

use URI::Escape;

#uri_escape($val);
#uri_unescape($val);

my $line="";
my $original_line="";
while ($line=<STDIN>) {
	$original_line=$line;
	chomp $line;

	##### Transformations Go Here
	#sucked $line =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;
	$line = &uri_escape($line);

	print $line;
} 