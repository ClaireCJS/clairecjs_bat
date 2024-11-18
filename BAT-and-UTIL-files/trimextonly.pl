while ($line=<STDIN>) {
    #$line=~ s/^.*\\//g;     print $line;
    #^old only worked with backslash delimiters
    #vnew works with both slash and backslash
     $line =~ s/^.*\.([^\.]+)$/$1/g; $line =~ tr/[A-Z]/[a-z]/; print $line;
}
