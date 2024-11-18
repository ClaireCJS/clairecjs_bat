
##USAGE: to generate script to go to next folder: go-to-nexts-directory-generator.pl current_directory_name          >script_to_run
##USAGE: to generate script to go to prev folder: go-to-nexts-directory-generator.pl current_directory_name PREVIOUS >script_to_run




my $DEBUG               =    0;			#set to 1 to debug, but nd.bat wont work when calling this in that mode
my $DIRECTORY_SEPARATOR = "\\";			#set to \\ for windows \/ for unix

##### I could probably figure this out in perl, but since I am calling this from "nd.bat" (next directory), I simply pass it %_CWP (the current working path)
my $starting_dir=$ARGV[0];
if ($DEBUG) { print "echo starting_dir=\"$starting_dir\"\n"; }

my $PREVIOUS=0;
if ($ARGV[1] eq "PREVIOUS") { $PREVIOUS=1;  }			#this will be slower until I code "check if previuos is a folder or not"

##### Now we reduce the current folder down to get the parent folder's name:
my $parent = $starting_dir;
$parent =~ s/[\\\/][^\\\/]*$//i;
$parent .= $DIRECTORY_SEPARATOR;
if ($DEBUG) { print "echo parent=\"$parent\"\n"; }

##### Now we change into the parent folder, and compile a list of everything in it:
chdir("$parent");
my @files   = <*>;
my @folders = sort {uc($a) cmp uc($b)} @files;
if ($DEBUG) { print "echo folders is: @folders \n"; for ($i = 0; $i <= @folders; $i++) { print "echo Folders[$i]=$folders[$i]\n"; } }

##### This list is folder names only, not full path names, so we must take our starting folder, and strip off everything except the last folder name:
my $target_dir = $starting_dir;
$target_dir =~ s/^(.*[\\\/])([^\\\/]*)$/$2/i;
my $base_dir = $1;

##### Now we go through our list of subfolders, and compare it to the original starting folder we are in:
if ($DEBUG) { print "echo ------------ match searching next... target_dir = $target_dir\n"; }
my $index=0;
my $max_index=@folders - 1;
my $FOUND=0;
my $direction=1;
if ($PREVIOUS) { $direction="-1"; }
while ((!$FOUND) && ($index <= $max_index)) {
	if ($DEBUG) { print "echo * Checking if \$folders[$index] ($folders[$index]) eq \$target_dir ($target_dir)...\n"; }
	if (($folders[$index] eq $target_dir) && (-d $target_dir)) {
		$FOUND=1;
		if ($DEBUG) { print "echo ******** match found!=\$folders[$index]=\"$folders[$index]\"\n"; }
	}
	$index += $direction;
	if ($DEBUG) { print "echo * index is now $index: \$folders[$index]=\"$folders[$index]\"\n"; print "echo check if !-d $base_dir$folders[$index] !!! \n";	if (-d "$base_dir$folders[$index]") { print "echo IT EXISTS!\n"; } else { print "echo IT DOES NOT EXIST!\n"; } }
	while ((!-d "$base_dir$folders[$index]") && ($index <= $max_index)) { 
		$index += $direction; 
		if ($DEBUG) { print "echo + index is now $index: \$folders[$index]=\"$folders[$index]\"\n"; }
	}		
}


##### Now we know our target for sure!
my $full_target = $base_dir.$folders[$index].$DIRECTORY_SEPARATOR;
if ($DEBUG) { print "echo * At this point, next folder should be=\"$folders[$index]\" (index=$index)\necho Also: base_dir=$base_dir\necho Thus: \$full_target is \"$full_target\"\n"; }

##### This works, but once the script is done, you return back. Obviously we need to echo out the command and have this piped to another script which we run...
#if (!chdir($full_target)) { if ($DEBUG) { print "ERROR: Could not change into $full_target\n"; } }

$full_target =~ s/\\\\$/\\/;		#double backslash at end

##### OUTPUT to be redirected to a script which is then run:
print "   \"$full_target\"\n";
print "cd \"$full_target\"\n";
