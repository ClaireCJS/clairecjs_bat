package CharacterEncodingFlaws;
use strict;
use warnings;
use Exporter 'import';
our @EXPORT = qw(fix_common_character_encoding_flaws);

sub fix_common_character_encoding_flaws {
	my $s = $_[0];

	##### dashes #####
	$s =~ s/\-\-([^>])/\x{2014}$1/g;		# -- -> em dash, unless it looks like -->

	##### apostrophes #####
	# These mojibake sequences arrive here after UTF-8 decoding, so they are
	# character sequences now, not raw bytes.
	$s =~ s/\x{00E2}\x{0080}\x{0099}/\x{2019}/g;	# mojibake right apostrophe
	$s =~ s/\x{00E2}\x{20AC}\x{2122}/\x{2019}/g;	# mojibake right apostrophe
	$s =~ s/\x{00E2}\x{0080}\x{0098}/\x{2019}/g;	# mojibake left apostrophe
	$s =~ s/\x{00E2}\x{20AC}\x{02DC}/\x{2019}/g;	# mojibake left apostrophe
	$s =~ s/[\x{2018}\x{2032}'`]/\x{2019}/g;		# apostrophe-ish chars
	$s =~ s/â€™/’/g;								# ths thing

	##### quotes #####
	$s =~ s/\x{0021}\x{201C}/\x{0021}\x{201D}/g;	# !“->!” - exclamation + left quote  exclamation + right quote
	$s =~ s/\x{201E}/\x{201C}/g;					# German low quote -> left quote

	return($s);
}

1;
