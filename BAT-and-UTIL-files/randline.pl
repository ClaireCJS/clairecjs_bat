#!perl

if ($ENV{"MAKE_IT_CD"} eq "1")            { $CD=1; print "*cd \""; }

my    @LINES=<STDIN>;
$line=$LINES[int(rand(@LINES))];        if ($CD) { chomp($line); }
print $line;                            if ($CD) { print "\"\n"; }





