#!/usr/local/bin/perl
if ($ARGV[0] eq "-v") { print "\nDriver Letter Remapper v2.0 (20041230)\n\n"; exit; }

#USAGE: echo c:\filename | remap        would echo "c:\filename" (no change to static drive letters unless REMAP<machinename> environment variable is specified.  However, %HD environment variables still substituted, see below)
#USAGE: echo c:\filename | remap c,s    would echo "s:\filename"
#USAGE: echo c:\filename | remap c,FRED would echo "FRED:\filename"

#####IMPORTANT SIDE-EFFECT:
#If the beginning of a line is HDxxG: , it is an implicit environment variable reference
#referring to a specific harddrive, ie %HD25G, %HD80G, %HD80G2, %HD80G3, etc.
#In this case, it checks the environment for such variable and
#subtitutes it in.  For instance, if %HD40G is "C:", then remap
#will take the line:    HD40G:\autoexec.bat
#and transform it into: c:\autoexec.bat

#NOTE: even tho we're talking env vars, DO NOT begin line with a "%".  
#There's no way to create this easily.  It will probably still work though, thanks to my regex use. Just not advised.

#This feature allows a single playlist (or other filelist) to be
#generated from multiple computers in such a manner that any of those
#multiple computers can still get accurate drive letters, assuming its
#environment is set up correctly.


my @real=(),my @mapped=(),my $line="";

#print "ARGV is ".@ARGV;

##### If no arguments were passed, check to see if an environment variable "%remap<machinename>" exists. 
##### %machinename is also an environment variable.
my $machinename = $ENV{"MACHINENAME"};
my $remapenv    = "";
if ($machinename ne "") { $remapenv = $ENV{"REMAP$machinename"}; }
if ((@ARGV == 0) && ($remapenv ne "")) { push(@ARGV,split(/\s+/,$remapenv)); }

#print "\nARgv    is @ARGV\n";
#print "\nARGV[0] is $ARGV[0]\n";
#print "\nARGV[1] is $ARGV[1]\n";
#exit;
foreach (@ARGV) {
    if ($_ =~ /,/) {
        ($realdriveletter,$mappeddriveletter)=split(/,/,"$_");
        next if $realdriveletter =~ /^$mappeddriveletter$/i;
        push(@real,  $realdriveletter);
        push(@mapped,$mappeddriveletter);
    }
}
while ($line=<STDIN>) {
    chomp $line;
    if ($line =~ /^%?(HD[0-9]+G[0-9]*):/) {
        my $env = $ENV{$1};
        my $s = "%?" . $1;
        if ($env ne "") { $line =~ s/$s/$env/; }
    } else {
        for (my $i=0; $i < @real; $i++) {
            if ($line =~ /^($real[$i]:)/i) {
                $line =~ s/$1/$mapped[$i]:/;
                last;
            }
        }
    }
	$WINDOWS=1;
    if ($WINDOWS) { $line =~ s$\/$\\$g; }
    if ($UNIX)    { $line =~ s$\\$\/$g; }
    print "$line\n";
}#endwhile
