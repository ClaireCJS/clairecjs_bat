while ($line=<STDIN>) {
    $line=~ s/\..{1,5}?$//; print $line;
}
