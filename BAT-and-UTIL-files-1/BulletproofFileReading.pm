package BulletproofFileReading;

use strict;
use warnings;
use Exporter 'import';
use Encode qw(decode FB_CROAK);
use utf8;

our @EXPORT = qw(
	decode_mixed_line
);


sub decode_mixed_line {
	#USAGE:	my $line = decode_mixed_line($raw);
	#USAGE: # On raw input, chomp may leave \r behind on CRLF files, so strip line ending explicitly:
	#USAGE: $line =~ s/\r?\n\z/ /;
	#USAGE: $line =~ s/[\r\n]+/ /g;
	#USAGE: $line =~ s/\n/ /ig;

	my ($raw) = @_;
	my $out = "";
	my $utf8_chunk;

	pos($raw) = 0;

	while (pos($raw) < length($raw)) {

		# Fast path: plain ASCII bytes
		if ($raw =~ /\G([\x00-\x7F]+)/gc) {
			$out .= $1;
			next;
		}

		# Valid UTF-8 sequence starting at the current byte position
		if ($raw =~ /\G(
				[\xC2-\xDF][\x80-\xBF]                            |   # 2-byte UTF-8
				\xE0[\xA0-\xBF][\x80-\xBF]                        |   # 3-byte UTF-8 (special low bound)
				[\xE1-\xEC\xEE-\xEF][\x80-\xBF]{2}                |   # 3-byte UTF-8
				\xED[\x80-\x9F][\x80-\xBF]                        |   # 3-byte UTF-8 (surrogate-safe)
				\xF0[\x90-\xBF][\x80-\xBF]{2}                     |   # 4-byte UTF-8 (special low bound)
				[\xF1-\xF3][\x80-\xBF]{3}                         |   # 4-byte UTF-8
				\xF4[\x80-\x8F][\x80-\xBF]{2}                         # 4-byte UTF-8 (special high bound)
			)/xgc) {
			$utf8_chunk = $1;
			$out .= decode('UTF-8', $utf8_chunk, FB_CROAK);
			next;
		}

		# One stray non-UTF-8 byte: interpret JUST THAT BYTE as Windows-1252.
		# This is the crucial part that lets files survive mixed encodings.
		$raw =~ /\G(.)/sgc;
		$out .= decode('Windows-1252', $1);
	}

	return $out;
}