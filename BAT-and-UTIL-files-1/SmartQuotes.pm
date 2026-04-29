package SmartQuotes;

use strict;
use warnings;
use Exporter 'import';
use utf8;

our @EXPORT = qw(
	replace_dumb_quotes_with_smart_quotes 
	replace_quotes_with_smart_quotes 
	replace_smart_quotes
);


sub replace_smart_quotes{
	return replace_quotes_with_smart_quotes (@_);
}
sub replace_dumb_quotes_with_smart_quotes {
	return replace_quotes_with_smart_quotes (@_);
}
sub replace_quotes_with_smart_quotes {
	#converted from my python function with chatgpt
	my ($text) = @_;
	return "" if !defined($text) or $text eq "";
	return "“”" if $text eq '""';
	return "“"  if $text eq '"';

	# Basic edge-replacement of first/last quotes
	$text =~ s/^"/“/;
	$text =~ s/"$/”/;

	my @chars = split //, $text;
	my @result;
	my $in_quotes = 0;
	my $last_non_space = "";
	my $char_used;

	for (my $i = 0; $i < @chars; $i++) {
		my $char = $chars[$i];
		my $prev  = $i > 0           ? $chars[$i-1] : "";
		my $pprev = $i > 1           ? $chars[$i-2] : "";
		my $next  = $i < $#chars     ? $chars[$i+1] : "";
		my $nnext = $i < $#chars - 1 ? $chars[$i+2] : "";

		if ($char eq '“') { $in_quotes = 1; }
		if ($char eq '”') { $in_quotes = 0; }

		if ($char eq '"') {							#[chatgpt:2025/05/19]
			if ($prev =~ /^[\[\(\{<¡!¿“]$/) {		#[chatgpt:2025/05/19]	#possibly remove exclaimation point
				$char_used = "“";					#[chatgpt:2025/05/19]
				$in_quotes = 1;						#[chatgpt:2025/05/19]
			}
			elsif ($prev =~ /^\s?$/ && $next =~ /^\s?$/) {
				if ($last_non_space eq "”") {
					$char_used = "“";
					$in_quotes = 1;
				} elsif ($last_non_space eq "“") {
					$char_used = "”";
					$in_quotes = 0;
				} elsif (($last_non_space =~ /\p{Punct}/ && $last_non_space ne "“" && $nnext =~ /\p{Alpha}/)
				      || ($last_non_space =~ /\p{Alpha}/ && $nnext =~ /\p{Alpha}/)) {
					$char_used = "“";
					$in_quotes = 1;
				} else {
					$char_used = "”";
					$in_quotes = 0;
				}
			} elsif ($prev eq " " && $next =~ /\p{Alpha}/ && $last_non_space ne ".") {
				$char_used = "“";
				$in_quotes = 1;
			} elsif ($prev =~ /\p{Punct}/ || $prev =~ /\p{Alpha}/) {
				$char_used = "”";
				$in_quotes = 0;
			} elsif (($prev eq "" || $prev =~ /\p{Punct}/) && $last_non_space ne "“") {
				$char_used = "“";
				$in_quotes = 1;
			} else {
				$char_used = $in_quotes ? "”" : "“";
				$in_quotes = !$in_quotes;
			}
			push @result, $char_used;
		} else {
			$char_used = $char;
			push @result, $char;
		}

		if ($char ne " ") {
			$last_non_space = ($char_used eq "“" || $char_used eq "”") ? $char_used : $char;
		}
	}

	my $result = join("", @result);

	#SUSPEND: $result =~ s/!“/!”/g;				# kludge bug fix

	return $result
}

1;
