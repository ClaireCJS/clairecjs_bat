package CommandLine;

use strict;
use warnings;
use Exporter 'import';

our @EXPORT = qw(
	fix_invalid_command_line_characters
);


sub fix_invalid_command_line_characters {
	#USAGE: line = &fix_invalid_command_line_characters($line):
	my $line = $_[0];
	$line =~ s/"/'/g;							# change quotes to apostrophes so these can be used as a quoted command line argument which we may not want to do in certain situations
	$line =~ s/\|/│/g;
	$line =~ s/</⧼/g;				
	$line =~ s/>/⧽/g;				
	return($line);
}

