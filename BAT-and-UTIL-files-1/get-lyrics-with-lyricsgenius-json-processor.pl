#!/usr/bin/perl

use strict;                                                 # use code strictness
use warnings;                                               # use good warnings
use JSON;                                                   # import library functionality for JSON 
use Encode;                                                 # import library functionality for UTF-8 
binmode STDOUT, ":encoding(UTF-8)";                         # Set STDOUT to handle UTF-8

my $json_text;                                              # downloaded .JSON file as string
my $data;                                                   # just the section of the JSON called “data” 
my $lyrics;                                                 # just the section of the data called “lyrics” 
my $title;                                                  # just the section of the data called “title” 

# Get our data:                                             # Retrieve our input data from a JSON file
$json_text = do { local $/; <STDIN> };                      # Read JSON input from STDIN
$json_text = Encode::decode('UTF-8', $json_text);           # Decode the JSON text from UTF-8
$data = decode_json($json_text);                            # Parse JSON data

# Extract values:                                           # Extract lyrics and title
$lyrics = $data->{"lyrics"};                                # Extract lyrics and title
$title  = $data->{"title" };                                # Extract lyrics and title

# Apply transformations:                                    # Apply transformations:    
$lyrics =~ s/\\n/\n/ig;                                     # Replace “\n” with actual newlines
$lyrics =~ s/[0-9] contributors?//ig;                       # Remove  “X contributors” at the beginning
$lyrics =~ s/\Q$title\E\s+lyrics//ig;                       # Remove  “{title} lyrics” from the beginning
while ($lyrics =~  /(Embed|You might also like)\s*$/i) {    # Remove  “Embed” and “You might also like” until neither are present
       $lyrics =~ s/(Embed|You might also like)\s*$//i      # Remove  “Embed” and “You might also like” until neither are present
}                                                           # Remove  “Embed” and “You might also like” until neither are present

print $lyrics;                                              # Print modified lyrics

