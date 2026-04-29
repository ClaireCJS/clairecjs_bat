package CharacterEncodingFlaws;
use strict;
use warnings;
use Exporter 'import';
our @EXPORT = qw(fix_common_character_encoding_flaws);

sub fix_common_character_encoding_flaws {
	my $s = $_[0];

	#dashes			
	$s =~ s/\-\-([^>])/—$1/g;			# fix “--” which is an archaic way of representing “—” ... Although this really should be turned into “——” if we are in a monospaced situation

	#apostrophes
	$s =~ s/â€™/’/g;					# mojibake right apostrophe sequence
	$s =~ s/€™/’/g;						# partial mojibake
	$s =~ s/\x{00E2}/’/g;				# bare â → ’
	$s =~ s/[′'`]/’/g;					# normal apostrophe-ish chars → ’

	#quotes
	#$s =~ s/’’/’/g;
	$s =~ s/!“/!”/g;					# copied from lyric-postprocessor: kludge bug fix
	$s =~ s/„/”/g;

	return($s);
}									                            


