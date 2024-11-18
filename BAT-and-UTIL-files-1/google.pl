use strict;
use warnings;
use URI::Escape;

sub main {
    my @args = @ARGV;

    # Reconstruct the query
    my @processed_args = map {
        if ($_ =~ /^".*"$/) {
            # Argument is already quoted, use as is
            $_
        } elsif ($_ =~ /\s/) {
            # Argument contains spaces, wrap it in double quotes
            qq("$_")
        } else {
            $_
        }
    } @args;

    my $query = join(' ', @processed_args);

    if (!$query) {
        print "Please provide a search query.\n";
        exit(1);
    }

    # Replace '+' signs with a placeholder
    $query =~ s/\+/___PLUS___/g;

    # URL-encode the query
    my $encoded_query = uri_escape($query);

    # Replace '%20' with '+'
    $encoded_query =~ s/%20/+/g;

    # Replace the placeholder with '%2B'
    $encoded_query =~ s/___PLUS___/%2B/g;

    # Construct the URL
    my $url = 'http://www.google.com/search?q=' . $encoded_query;

    # Open the URL
    system("start", "", $url);

    exit(0);
}

main();
