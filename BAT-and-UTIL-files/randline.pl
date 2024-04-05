#!perl

if ($ENV{"MAKE_IT_CD"} eq "1")      { $CD=1; print "cd \""; }			#was *cd from 2000-202404 but now that file-count maintenance has been added to our cd-alias.bat we want to take advantage of that

my    @LINES=<STDIN>;
$line=$LINES[int(rand(@LINES))];    if ($CD) { chomp($line); }
print $line;                        if ($CD) { print "\"\n"; }





