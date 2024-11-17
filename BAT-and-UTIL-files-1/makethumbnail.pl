###### CONSTANTS ######
my $DEFAULT_THUMB_EXTENSION     = "tnb";
my $DEFAULT_LARGEST_SIDE        = 300;
my $DEFAULT_OVERWRITE           = 0;
my $DEFAULT_VERBOSE             = 0;                    #
my $DEFAULT_RECURSE             = 0;
my $DEFAULT_THRESHOLD           = 1.5;          #don't make a thumbnail if both dimensions are less than 1.5*LARGEST_SIDE
my $DEFAULT_SIZE_THRESHOLD      = "75000";

###### DEBUGS ######
my $DEBUG_HASH = 0;				#another verbosity

###### PACKAGES ######
use GD;
use Image::GD::Thumbnail;
use Image::Size;                        
use strict;
use vars qw ( $verbose );

###### GLOBALS ######
my %ARGS=();
my $tmpfile="";
my $tmp1="";
my $tmp2="";
my $junk="";


#################################### MAIN ####################################
### Get options:
&hashargv;
local $verbose          = ((defined $ARGS{v}) && ($ARGS{v}ne"0")) || $DEFAULT_VERBOSE;
my $overwrite           = ((defined $ARGS{o}) && ($ARGS{o}ne"0")) || $DEFAULT_OVERWRITE;
my $recurse             = ((defined $ARGS{s}) && ($ARGS{s}ne"0")) || $DEFAULT_RECURSE;
my $max_dimension       = $ARGS{m} || $DEFAULT_LARGEST_SIDE;
my $thresholdfactor     = $ARGS{t} || $DEFAULT_THRESHOLD;
if ($ARGS{t} == 0)      { $thresholdfactor = 0; }
my $notifsmallerthan    = $ARGS{u} || $DEFAULT_SIZE_THRESHOLD;
my $threshold           = $max_dimension * $thresholdfactor;

#if (defined $ARGS{o}) { print "overwrite is defined\n"; }
#if ($ARGS{o}ne"0") { print "overwrite is != 0\n"; }
#if ($ARGS{o}eq"0") { print "overwrite is == 0\n"; }
#print "overwrite=$overwrite\n";#

##### Give info on current execution status:
        print "* Recurse:              " . ($recurse  ?"ON":"OFF") . "\n";
        print "* Overwrite:            " . ($overwrite?"ON":"OFF") . "\n";
        print "* Max Dimension:        " . $max_dimension          . "\n";
        print "* Threshold Factor:     " . $thresholdfactor        . "\t(images less than $threshold width or height will not have thumbnails made)\n";
        print "* Skip if smaller than: " . $notifsmallerthan       . "\t(images lsss than $notifsmallerthan in size will not have thumbnails made)\n";



### Do proper execution mode:
if (-e $ARGV[0]) { 
        ### Make one thumbnail:
        &MakeOneThumb({source_file=>@ARGV[0],verbose=>$verbose,overwrite=>$overwrite}); 
        exit; 
} elsif (defined $ARGS{d}) {
        my $dir = $ARGS{d} || ".";
        if (!-d $dir)   { die("\nDirectory of $dir does not exist!\n"); }


		my ($numthumbs,$numdirs)=&MakeThumbnailsInDirectory({dir=>$dir,verbose=>$verbose,overwrite=>$overwrite,recurse=>$recurse,largest_side=>$max_dimension,threshold=>$threshold,not_if_smaller_than=>$notifsmallerthan});   
        print "\n\n*** There were $numthumbs thumbnails created in $numdirs directories.\n";
        exit;
}#endif
&usage;         ### Do usage if they messed up
#################################### MAIN ####################################

########################################################################################
sub MakeThumbnailsInDirectory {
        my $options             = $_[0];
        my $dir                 = $options->{dir};
        my $overwrite           = $options->{overwrite}                 || $DEFAULT_OVERWRITE;
        my $verbose             = $options->{verbose}                   || $DEFAULT_VERBOSE;
        my $recurse             = $options->{recurse}                   || $DEFAULT_RECURSE;
        my $max_dimension       = $options->{largest_side}              || $DEFAULT_LARGEST_SIDE;
        my $threshold           = $options->{threshold}                 || $DEFAULT_THRESHOLD;
        my $notifsmallerthan    = $options->{not_if_smaller_than}       || $DEFAULT_SIZE_THRESHOLD;
        my $numthumbs           = 0;

		#DEBUG: 
		print "\n\n******* \$ARGS{m} is $ARGS{m}.\nMax dimension is $max_dimension\n\n";

        print "\n* Making thumbnails in: $dir"; 
        my $numdirs=0;
        my $numthumbs=0;
        my ($FILES,$SUBDIRS) = &GetContentsOfDirectory($dir);
        $numdirs++;
        foreach $tmpfile (@$FILES) {
                $numthumbs += &MakeOneThumb({source_file=>$tmpfile,overwrite=>$overwrite,verbose=>$verbose,largest_side=>$max_dimension,threshold=>$threshold,not_if_smaller_than=>$notifsmallerthan});
                #DEBUG:print "numthumbs is currently $numthumbs after file $tmpfile...\n";#
        }#endforeach
        foreach $tmpfile (@$SUBDIRS) {
                #print "Dir: $tmpfile\n";#
                if ($recurse) { 
                        ($tmp1,$tmp2)=&MakeThumbnailsInDirectory({dir=>$tmpfile,overwrite=>$overwrite,verbose=>$verbose,recurse=>$recurse,larget_side=>$max_dimension,threshold=>$threshold}); 
                        #DEBUG:print "tmp1=$numthumbs\n";#
                        $numthumbs += $tmp1;
                        $numdirs   += $tmp2;
                }
        }#endforeach
        #DEBUG: print "Returning $numthumbs,d=$numdirs...\n";#
        return($numthumbs,$numdirs);
}#endsub MakeThumbnailsInDirectory
########################################################################################



####################################################################################
sub MakeOneThumb {
        my $options             = $_[0];
        my $source_file         = $options->{source_file}               || "";
        my $extension           = $options->{extension}                 || $ARGS{e} || $DEFAULT_THUMB_EXTENSION;
        my $max_dimension       = $options->{largest_side}              || $ARGS{m} || $DEFAULT_LARGEST_SIDE;
        my $overwrite           = $options->{overwrite}                 || $ARGS{o} || $DEFAULT_OVERWRITE;
        my $verbose             = $options->{verbose}                   || $ARGS{v} || $DEFAULT_VERBOSE;
        my $threshold           = $options->{threshold}                 || $ARGS{t} || $DEFAULT_THRESHOLD;
        my $notifsmallerthan    = $options->{not_if_smaller_than}       || $ARGS{u} || $DEFAULT_SIZE_THRESHOLD;
        my $srcImage;
        my $x;
        my $y;

        ##### We can't generate thumbnails for thumbnails!:
        if ($srcImage =~ /\.$DEFAULT_THUMB_EXTENSION$/i) { return(0); }

        ##### Determine target file:
        my $target_file         = $source_file;
        $target_file            =~ s/^(.*)(...)/$1$extension/;


        ##### Verbose info:
        if ($verbose) {
                print "\nGenerating thumnail:";
                print "\n\tsource file:\t$source_file";
                print "\n\ttarget file:\t$target_file";
                print "\n\textension:\t$extension";
                print "\n\tlargest side:\t$max_dimension";
                print "\n\toverwriting:\t" . ($overwrite?"Yes":"No");
                print "\n\tnot if smaller than:\t$notifsmallerthan";
                print "\n";
        }#endif 

        ##### Check for source file existence:
        if (!-e $source_file) { 
                die("\nsource_file of $source_file does not exist!!\n");
        }#endif

        ##### Do not regnerate thumbnail if we aren't supposed to overwrite:
        if (-e $target_file) { 
                if ($verbose) { print "* Target file of $target_file already exists..."; }
                if ($overwrite) {
                        if ($verbose) { print "Overwriting!\n"; }
                } else {
                        if ($verbose) { print "Skipping!\n"; }
                        return(0); 
                }
        }#endif


        ##### check the extension:
        if ($source_file =~ /\.jpe?g$/i) {
        } elsif ($source_file =~ /\.png$/i) {
        } elsif ($source_file =~ /\.xbm$/i) {
        } elsif ($source_file =~ /\.xpm$/i) {
        } elsif ($source_file =~ /\.gd2$/i) {
        } elsif ($source_file =~ /\.gd$/i) {
        } else {
                if ($verbose) { print "* Cannot generate thumbnail for unsupported extension. File: $source_file\n"; }
                return(0);
        }


        ##### Do not generate a thumbnail if the file's size is too small:
        ($junk,$junk,$junk,$junk,$junk,$junk,$junk,$tmp1,$junk,$junk,$junk,$junk,$junk) = stat($source_file);
        if ($tmp1 < $notifsmallerthan) {
                print "_";
                return(0);
        }#endif

        ##### Load your source image
        open IN, $source_file || die "Could not open $source_file";
        if ($source_file =~ /\.jpe?g$/i) {
                $srcImage = GD::Image->newFromJpeg(*IN);
        } elsif ($source_file =~ /\.png$/i) {
                $srcImage = GD::Image->newFromPng(*IN);
        } elsif ($source_file =~ /\.xbm$/i) {
                $srcImage = GD::Image->newFromXbm(*IN);
        } elsif ($source_file =~ /\.xpm$/i) {
                $srcImage = GD::Image->newFromXpm(*IN);
        } elsif ($source_file =~ /\.gd2$/i) {
                $srcImage = GD::Image->newFromGd2(*IN);
        } elsif ($source_file =~ /\.gd$/i) {
                $srcImage = GD::Image->newFromGd(*IN);
        } else {
                if ($verbose) { print "* Cannot generate thumbnail for unsupported extension. File: $source_file\n"; }
                close IN;
                return(0);
        }
        close IN;


        ##### Get the dimensions, and suppress thumbnail generation if it's too small:
        ($x,$y) = &imgsize($source_file);
        if (($x < $threshold) || ($y < $threshold)) {
                if ($verbose)   { print "\n* Size of $x"."x"."$y for image $source_file is too small to bother making a thumbnail (threshold=$threshold)"; }
                else                    { print "-"; }
                return(0);
        }#endif

        
        ##### Create the thumbnail from it:
        #DEBUG:print "\nmaking...";#
        my ($thumb,$x,$y) = Image::GD::Thumbnail::create($srcImage,$max_dimension);
        
        ##### Save your thumbnail
        open OUT, ">$target_file" or die "Could not save ";
        binmode OUT;
        print OUT $thumb->jpeg;
        close OUT;

        #DEBUG:print "\nmakeonethumb returning 1...";#
        if (!$verbose) { print "."; }
        return(1);
}#endsub MakeOneThumb
####################################################################################
########################################
sub hashargv {
		#DEBUG(USELESS):print "\n\n FUCK! verbose=$verbose\n\n";
        my ($argletter,$value);
		if ($verbose) { print "\n* Processing command-line arguments... (&hashargv;)\n"; }
        foreach my $arg (@ARGV) {
                if ($arg =~ /^-(.)(.*)$/) {
                        $argletter = lc($1);
                        $value     = $2;
                        if ($DEBUG_HASH) { print "\$ARGS{$argletter}=$value;\n"; }
                        $ARGS{$argletter}=$value;
                }
        }
}#endsub hashargv
########################################

######################################################################################################
sub GetContentsOfDirectory {
        #USAGE: ($filesArrayRef,$subdirsArrayRef) = &GetContentsOfDirectory($dir);
        my $dirname = $_[0];
        my @files       = ();
        my @subdirs     = ();
        my $entity      = "";
        my $tmp = "";

        opendir(DIR, $dirname) or die "FATAL ERROR: can't open directory \"$dirname\": $!";
        while (defined($entity = readdir(DIR))) { 
                next if ($entity =~ /^\.{1,2}/);
                $tmp = "$dirname/$entity";
                if    (-f $tmp) { push(@files,  $tmp); }
                elsif (-d $tmp) { push(@subdirs,$tmp); }
                else {
                        print "WARNING: unknown entity of $tmp in dir $dirname...\n";
                }#endeif
        }#endwhile
        closedir(DIR);
        return \@files, \@subdirs;
}#endsub GetContentsOfDirectory
######################################################################################################


########################################################
sub usage {
print <<__EOF__;

USAGE:
        $0 [filename first for single thumbnail mode only] [options] 

OPTIONAL PARAMETERS:   (values shown are the default values)
        -d -s$DEFAULT_RECURSE -m$DEFAULT_LARGEST_SIDE -e$DEFAULT_THUMB_EXTENSION -v$DEFAULT_VERBOSE -o$DEFAULT_OVERWRITE -v$DEFAULT_VERBOSE -t$DEFAULT_THRESHOLD -u$DEFAULT_SIZE_THRESHOLD
                -d: do all files in current directory, or specify a directory
                -s: recurse directories (0=no,1=yes,default=$DEFAULT_RECURSE);
                -m: set max side size 
                -t: set dimensional threshold factor 
                        This supresses thumbnail generation if the image's 
                        width or length is less than the factor * max_side_size.
                        If your max size is 300, and the factor is 1.5, then
                        any image that has width less than 450 or a length less
                        then 450 will not have a thumbnail generated.
                -u: set size threshold factor
                        This supresses thumbnail generation if the original
                        image's filesize is less than the size specified
                -e: use thumbnail extension 
                -o: overwrite existing thmbnails (0=no,1=yes,default=$DEFAULT_OVERWRITE)
                -v: verbosity level 

EXAMPLES:
        $0 whatever.jpg
        $0 something.jpg -m300 -eTHM -o -v1 -t1.5 -u100000

__EOF__
}#endsub usage
########################################################
