#!/usr/bin/perl
use strict;
use warnings;
use JSON;
use Encode;

# Set STDOUT to handle UTF-8
binmode STDOUT, ":encoding(UTF-8)";

# Read JSON input from STDIN
my $json_text = do { local $/; <STDIN> };

# Decode the JSON text from UTF-8
$json_text = Encode::decode('UTF-8', $json_text);

# Parse JSON data
my $data = decode_json($json_text);

# Extract lyrics and title
my $lyrics = $data->{"lyrics"};
my $title = $data->{"title"};

# Apply transformations
$lyrics =~ s/\\n/\n/ig;                       # Replace \n with actual newlines
$lyrics =~ s/[0-9] contributors?//ig;         # Remove "X contributors" at the beginning
$lyrics =~ s/\Q$title\E\s+lyrics//ig;         # Remove "{title} lyrics" from the beginning
$lyrics =~ s/You might also like//ig;
my $thing;
my @THINGS=("verse", "guitar solo", "bridge", "chorus");
foreach $thing (@THINGS) {
	$lyrics =~ s/\[$thing *[0-9]*\]:?\n?//ig;
}
$lyrics =~ s/(Embed|You might also like)\s*$//i while $lyrics =~ /(Embed|You might also like)\s*$/i; # Remove "Embed" and "You might also like" until neither are present
$lyrics =~ s/\x{2019}/'/g;                   # Replace Unicode right single quotation mark with apostrophe
$lyrics =~ s/\x{0435}/e/g;                   # Replace Unicode right single quotation mark with apostrophe


# Print modified lyrics
print $lyrics;
