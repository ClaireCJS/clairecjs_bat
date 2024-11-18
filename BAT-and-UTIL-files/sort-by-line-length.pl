
@LINES=<STDIN>;
print sort { length($a) <=> length($b) } @LINES;

