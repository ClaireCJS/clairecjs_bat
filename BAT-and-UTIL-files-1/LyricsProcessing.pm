package LyricsProcessing;

use strict;
use warnings;
use Exporter 'import';
use utf8;

our @EXPORT = qw(
	@lyric_website_spam_patterns
);

our @lyric_website_spam_patterns = (
	qr/\*? (No|\[(duble|metrolyrics|lyrics[a-z]+|lyrics4all|sing365|[a-z\d]+lyrics[a-z\d]*|\[[a-z0-9]+ )\]) filter used/,
	qr/\*? ?Downloaded from: http:\/\/[a-z0-9_\-.\/]+/,
	qr/\*? ?Downloaded from: http:\/\/[^ ]+/,
	qr/Get tickets? as low as \$[\d\.]+/,
	qr/Album tracklist with lyrics/,
	qr/You might also like/,
	qr/^(.*[a-zA-Z])Embed\.?$/,
	qr/^[0-9]+ Contributors$/,
	qr/^encoding: utf-8$/,
	qr/^.* Lyrics$/,							# todo we could be probing and using the songtitle here to be more restrictive
);

1;
