$TARGET = $ARGV[0];
$TARGET =~ s/^\"//;				#remove...	
$TARGET =~ s/\"$//;				#...quotes
$TARGET =~ s/^[a-z]:\\*//i;		#remove drive letter
$TARGET =~ s/-flickr\\*$//i;	#remove "-flickr" off end of foldername
$TARGET =~ s/[\\\/]*$//;		#remove trailing [back]slashes
$TARGET =~ s/^..[\\\/]*$//;		#remove leading ..\
$TARGET =~ s/^.*[\\\/]//;		#remove leading any folder...    2015 test... 
								#DEBUG: #print "target is: ";
print $TARGET;
