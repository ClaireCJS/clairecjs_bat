# This is a very relaxed uniq.  The file doesn't have to be sorted. The case doesn't have to match.
$uctmp;
while(<>) {
	$uctmp=uc($_);
	if ($seen{$uctmp}) { next; }
    $seen{$uctmp}=1;
    print $_;
}
