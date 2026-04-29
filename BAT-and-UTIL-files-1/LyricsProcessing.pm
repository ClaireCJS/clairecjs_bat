package LyricsProcessing;

use strict;
use warnings;
use Exporter 'import';

our @EXPORT = qw(
	@lyric_website_spam_patterns
);

our @lyric_website_spam_patterns = (
	qr/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used/i,
	qr/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+/i,
	qr/\*? ?Downloaded from: http:\/\/[^ ]+/i,
	qr/Get tickets as low as \$[\d\.]+/i,
	qr/Album tracklist with lyrics/,
	qr/You might also like/i,
	qr/^(.*[a-zA-Z])Embed\.?$/i,
	qr/^[0-9]+ Contributors$/,
	qr/^.* Lyrics$/,							# todo we could be probing and using the songtitle here to be more restrictive
);

1;
