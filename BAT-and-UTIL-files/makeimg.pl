
#20080403 - dated comment found below!

use strict;

$|=1;

#### NOTE: $ENV{WIDTH} -- causes it to crunches the width to fit on screen.  My environm[ent].bat sets this to be equal to the width of the screen, using 4NT variables that return this value.  You will have better results of the WIDTH environment variable is set to your screen resolutoin width.

##### OPTIONS:									#[captioning options are in a separate section below]
my $SUPPRESS_HTML4_VIDEO_EMBED_WE_USE_FOR_IE=0;	#201510: Suppress old IE embedding
my $CHROME_VIDEO_WIDTH="1280";					#201510: New HTML5 video embedding
my  $WIDTH_DECREASE_FOR_TAGMODE=250;			#when showing tags to right of picture, it helps to squish picture a bit. By this much.
my $HEIGHT_DECREASE_FOR_TAGMODE=350;			#when showing tags to right of picture, it helps to squish picture a bit. By this much.
#20200824 - suddenly shit's way too wide wtf?!?!
my  $WIDTH_DECREASE_FOR_TAGMODE=350;			#when showing tags to right of picture, it helps to squish picture a bit. By this much.
my $HEIGHT_DECREASE_FOR_TAGMODE=450;			#when showing tags to right of picture, it helps to squish picture a bit. By this much.
												#100 for a decade, but set to 200 in 2015
my $MARGIN_X=55;								#decreased by 5 to 55, 200608, after years of being fine
my $MARGIN_Y=75;								#decreased by 5 to 75, 200608, after years of being fine
my $IMAGES_LINK_TO_THEMSELVES=1;				#click on an image to open it in a new window. useful? I dunno.  Wish I could make it so you could click on it and have it open with the default windows application to open that type.
my $STUPID_UNUSED_FLAG=1;						#formerly "$VERBOSE" - THIS ONE IS NOT!!!!!!!!!!!		#THIS SHOULD STAY 1!! ALWAYS!!! YES I'M STUPID! AND TOO LAZY TO FIX THIS! "Skeeter never hurt no one"

##### DEBUGS:
my $DEBUG_FIND_ATTRIB_LIST=0;
my $DEBUG_TAGREAD=0;				#set to 0 normally #!
my $verbose=0;						#THIS one is for debugging.		#used on 20040715 


##### LIBRARIES:
my $USEIMGLIB=1;					#if set to 0, breaks image crunching!!!!!!!!!!!!!!!!!!!
my $USECLIOLIB=1;					#only works if you have /perl/site/bin/Clio folder with Claire libraries

		if ($USECLIOLIB==1) {
			use Clio::PictureTag qw(all);
			use Clio::HTML qw(all);
			use vars qw($TAGFILE_NAME %tags %globaltags %captions);
		}
		if ($USEIMGLIB==1) {
			use Image::Size;						#is it really?		use Image::Magick;		#used by Image::Size
		}
		use vars qw(%postcaptionsFromTagfile);
		if ($ENV{"IMAGEINDEX_QUICK"} eq "1") { $STOP_LINKIFY=1; }

##### CAPTION-CREATION SUPPORT:
my $CREATE_CAPTIONS                   = 1;						#1 to display framework for caption creating
my $DEFAULT_BACKSTORY_TEXT            = "<B>BACKSTORY:</b> ";	#DO NOT CHANGE. Beginning with the word BACKSTORY bolded is a convention we hold dear. And :postcaption is a specific, special kind of caption that appears after the automated section of our captions, instead of before.
my $CAPTION_SAVE_FILEPATH             =   "c:\\\\";		        #NOTE: *DOUBLE_ESCAPED*, so "\" becomes "\\\\". 
my $CAPTION_SAVE_FILENAME             = "captions.tmp";         #NOTE: This + CAPTION_SAVE_FILENAME combine to be copied into clipboard for convenient file-saving.
my $DEFAULT_BACKSTORY_TEXTAREA_WIDTH  =  "700px";				#NOTE: CSS not HTML, so "px" necessary.
my $DEFAULT_BACKSTORY_TEXTAREA_HEIGHT =   "50px";				#NOTE: CSS not HTML, so "px" necessary.
my $DEFAULT_CAPTION_TEXTAREA_WIDTH    =  "800px";				#NOTE: CSS not HTML, so "px" necessary.
my $DEFAULT_CAPTION_TEXTAREA_HEIGHT   =   "50px";				#NOTE: CSS not HTML, so "px" necessary.
my $CAPTION_PREVIEW_FONT_SIZE         =   "11px";				#NOTE: CSS not HTML, so "px" necessary.
my $FILENAME_IN_CLIPBOARD_ALERT_TEXT  = " *** FILENAME TO SAVE IS COPIED TO THE CLIPBOARD! *** ";
my $CAPTION_SAVE_BUTTON_TEXT          = "#Save Captions  (SAVE IN C:\\!!!)";		#put a "#" in front of it because sometimes we accidentally copy the string into attrib.lst, and doing that makes it fail! lol

##### GLOBALS:
my $target=0;	#increments each time a link with target="" is created
my ($x,$y)=("","");
my ($resize_x,$resize_y)=("","");
my ($resize_x_tmp,$resize_y_tmp)=("","");
my ($resize_x_or_zero,$resize_y_or_zero);
my $line;
my $GENERATE;
my $filename;
my $CWDLAST;
my $CWD4PRINT;
my $ratio;
my $RECURSIVE4PRINT;
my $TITLE;
my $STUPID_UNUSED_FLAGSTR;
my $nothing;
my $date;
my $href;
my $time;
my $size;
my $tmpname;
my $tmptag;
my @tmptags=();
my $TAGMODE=0;
my $tmpdimension="";
my $tmp="";
my @YouTubeTags=();
my @FlickrTags=();
my $linkfilenameConverted="";
my $srcToUse="";



############ GET COMMAND-LINE ARGUMENTS:
#print "ARGV0 is $ARGV[0]\n";
my $CWD = $ARGV[0];
my $N   = $ARGV[1];		#$N? What a horrible variable name! Something to do with the total number of images?
my $O   = $ARGV[2];


############ GET REZ FROM ENV:
my $WIDTH="";
my $HEIGHT="";
# doing both does not preserve aspect ratio, would have to use a package to do that
#This gets modified later if $TAGMODE=1;
$resize_x = $ENV{"WIDTH"};
$resize_y = $ENV{"HEIGHT"};


############ COMMAND-LINE PROCESSING:
if (($N =~ /VERBOSE/i) || ($O =~ /VERBOSE/i)) {
    $N=""; $STUPID_UNUSED_FLAG=1;
}
if (($N =~ /TERSE|NONVERBOSE|QUICK|COMPACT/i) || ($O =~ /TERSE|NONVERBOSE|QUICK|COMPACT/i)) {
    $N=""; $STUPID_UNUSED_FLAG=0;
}
if ($STUPID_UNUSED_FLAG) { $STUPID_UNUSED_FLAGSTR="verbose"; } else { $STUPID_UNUSED_FLAGSTR="compact"; }
if (($N =~ /GENERATE/i) || ($O =~ /GENERATE/i)) { $GENERATE=1; }

############ SETUP
$CWD4PRINT = $CWD;
$CWD4PRINT =~ s/[\/\\]$//;
$CWDLAST = $CWD;
$CWDLAST =~ s/^.*[\/\\]//g;
$CWD .= "\\";

if ($ARGV[0] eq "") { $CWD=""; }




########### Look for attrib.lst in parent folders and such:
if (!-e $TAGFILE_NAME) {
	if ($DEBUG_FIND_ATTRIB_LIST) { print "\$TAGFILE_NAME $TAGFILE_NAME does not exist!\n"; }
	for (my $i=1; $i < 5; $i++) {						#we'll check 5 folders back
		$TAGFILE_NAME = "..\\" . $TAGFILE_NAME; 
		if ($DEBUG_FIND_ATTRIB_LIST) { print "**** Checking $TAGFILE_NAME\n"; }
		if (-e $TAGFILE_NAME) { 
			if ($DEBUG_FIND_ATTRIB_LIST) { print "\$TAGFILE_NAME $TAGFILE_NAME exists and was found (after $i additional tries)!\n"; }
			last; 
		}
	}		
} else {
	if ($DEBUG_FIND_ATTRIB_LIST) { print "\$TAGFILE_NAME $TAGFILE_NAME exists and was found!\n"; }
}




############ HEADER
$TITLE = "$CWD4PRINT - Image Index - $STUPID_UNUSED_FLAGSTR";
if ($GENERATE) { $TITLE="$CWDLAST"; }
if ($ENV{RECURSIVE} eq "1") { $RECURSIVE4PRINT="Recursive "; }
print qq[<head><title>$TITLE</title></head>
<!--


Re-packaged by _Claire_


cwd= $CWD <BR>
title= $TITLE <BR>
-->\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n];

if ($CREATE_CAPTIONS) {
	print <<__EOF1__;
<!-- for captions: begin -->
<script type='text/javascript'>

var allText='';
var browserName;
function assembleAllText() {
	var captions = document.getElementsByName('caption');
	allText='';
	for (var i = 0, caption; caption = captions[i]; i++) {
	   //alert("caption[" + i + "]=" + caption + "/tos=" + caption.toString() + "/val=" + caption.value);
	   allText = allText + caption.value.replace(/\\r?\\n/g, '<br>');
	   if (((i+1) % 2) == 0) {
		   allText = allText + "\\n";
	   }
	} 

	//update textarea at bottom of page with newly-assembled captions--massaged for in-browser display:
	textarea = document.getElementById('allText');
	textarea.innerHTML = allText.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\r?\\n/g, '<br />');	
}


function captionkeyup(event) {
	assembleAllText();
}



function CopyToClipboard(containerid) {
	if (document.selection) { 
		var range = document.body.createTextRange();
		range.moveToElementText(document.getElementById(containerid));
		range.select().createTextRange();
		document.execCommand("Copy"); 
		document.selection.empty();
		 //alert("text copied") 
	} else if (window.getSelection) {
		var range = document.createRange();
		 range.selectNode(document.getElementById(containerid));
		 window.getSelection().addRange(range);
		 document.execCommand("Copy");
		 window.getSelection().removeAllRanges();
		 //alert("text copied") 
	}
    return false;
}




function saveTextAsFile() {
	whichBrowser();
	alert(browserName);


	//copy filename to clipboard
	clipboard.copy({
		'text/plain': "$CAPTION_SAVE_FILEPATH$CAPTION_SAVE_FILENAME",
		//'text/html': '<i>here</i> is some <b>rich text</b>'
	  }).then(
		function(   ){console.log('success'    ); },
		function(err){console.log('failure',err); }
	);

	//assemble the caption one last time, in case any events were missed
	assembleAllText();

	//let the user know what's going on
	alert('$FILENAME_IN_CLIPBOARD_ALERT_TEXT');
	//alert("DEBUG INFO: File contents will be:\\n\\n" + allText);

	//create the file
	var textToWrite = allText;	   
	var textFileAsBlob = new Blob([textToWrite], {type:'text/plain'});
	var fileNameToSaveAs = document.getElementById("inputFileNameToSaveAs").value;

	//create the download link
	if (browserName=="Netscape") {	//Internet Explorer, actually! That's just how it identifies itself.
		window.navigator.msSaveBlob(textFileAsBlob, "$CAPTION_SAVE_FILEPATH$CAPTION_SAVE_FILENAME");
	} else {
		var downloadLink = document.createElement("a");
		downloadLink.download = fileNameToSaveAs;
		downloadLink.innerHTML = "Download File";
		if (window.webkitURL != null) {
			//Chrome allows the link to be clicked without actually adding it to the DOM.
			downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob);
		} else {
			//Firefox requires the link to be added to the DOM before it can be clicked.
			downloadLink.href = window.URL.createObjectURL(textFileAsBlob);
			downloadLink.onclick = destroyClickedElement;
			downloadLink.style.display = "none";
			document.body.appendChild(downloadLink);
		}

		//click the download link
		downloadLink.click();
	}
}

function destroyClickedElement(event) {
	document.body.removeChild(event.target);
}


function whichBrowser() {
	//ASSUME: browserName is implemented as a global variable to be freely used anywhere
 
	var nVer = navigator.appVersion;
	var nAgt = navigator.userAgent;
	browserName  = navigator.appName;
	var fullVersion  = ''+parseFloat(navigator.appVersion); 
	var majorVersion = parseInt(navigator.appVersion,10);
	var nameOffset,verOffset,ix;

	// In Opera 15+, the true version is after "OPR/" 
	if ((verOffset=nAgt.indexOf("OPR/"))!=-1) {
	 browserName = "Opera";
	 fullVersion = nAgt.substring(verOffset+4);
	}
	// In older Opera, the true version is after "Opera" or after "Version"
	else if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
	 browserName = "Opera";
	 fullVersion = nAgt.substring(verOffset+6);
	 if ((verOffset=nAgt.indexOf("Version"))!=-1) 
	   fullVersion = nAgt.substring(verOffset+8);
	}
	// In MSIE, the true version is after "MSIE" in userAgent
	else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
	 browserName = "Microsoft Internet Explorer";
	 fullVersion = nAgt.substring(verOffset+5);
	}
	// In Chrome, the true version is after "Chrome" 
	else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) {
	 browserName = "Chrome";
	 fullVersion = nAgt.substring(verOffset+7);
	}
	// In Safari, the true version is after "Safari" or after "Version" 
	else if ((verOffset=nAgt.indexOf("Safari"))!=-1) {
	 browserName = "Safari";
	 fullVersion = nAgt.substring(verOffset+7);
	 if ((verOffset=nAgt.indexOf("Version"))!=-1) 
	   fullVersion = nAgt.substring(verOffset+8);
	}
	// In Firefox, the true version is after "Firefox" 
	else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
	 browserName = "Firefox";
	 fullVersion = nAgt.substring(verOffset+8);
	}
	// In most other browsers, "name/version" is at the end of userAgent 
	else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) < 
			  (verOffset=nAgt.lastIndexOf('/')) ) 
	{
	 browserName = nAgt.substring(nameOffset,verOffset);
	 fullVersion = nAgt.substring(verOffset+1);
	 if (browserName.toLowerCase()==browserName.toUpperCase()) {
	  browserName = navigator.appName;
	 }
	}
	// trim the fullVersion string at semicolon/space if present
	if ((ix=fullVersion.indexOf(";"))!=-1)
	   fullVersion=fullVersion.substring(0,ix);
	if ((ix=fullVersion.indexOf(" "))!=-1)
	   fullVersion=fullVersion.substring(0,ix);

	majorVersion = parseInt(''+fullVersion,10);
	if (isNaN(majorVersion)) {
	 fullVersion  = ''+parseFloat(navigator.appVersion); 
	 majorVersion = parseInt(navigator.appVersion,10);
	}

	//document.write(''
	// +'Browser name  = '+browserName+'<br>'
	// +'Full version  = '+fullVersion+'<br>'
	// +'Major version = '+majorVersion+'<br>'
	// +'navigator.appName = '+navigator.appName+'<br>'
	// +'navigator.userAgent = '+navigator.userAgent+'<br>'
	//)
}


//<!-- clipboard: begin -->
var clipboard = {};

clipboard.copy = (function() {
  var _intercept = false;
  var _data; // Map from data type (e.g. "text/html") to value.

  document.addEventListener("copy", function(e) {
    if (_intercept) {
      _intercept = false;
      for (var key in _data) {
        e.clipboardData.setData(key, _data[key]);
      }
      e.preventDefault();
    }
  });

  return function(data) {
    return new Promise(function(resolve, reject) {
      _intercept = true; // Race condition?
      _data = (typeof data === "string" ? {"text/plain": data} : data);
      try {
        if (document.execCommand("copy")) {
          // document.execCommand is synchronous: http://www.w3.org/TR/2015/WD-clipboard-apis-20150421/#integration-with-rich-text-editing-apis
          // So we can call resolve() back here.
          resolve();
        } else {
          _intercept = false;
          reject(new Error("Unable to copy. Perhaps it's not available in your browser?"));
        }
      } catch (e) {
        _intercept = false;
        reject(e);
      }
    });
  };
}());

clipboard.paste = (function() {
  var _intercept = false;
  var _resolve;
  var _dataType;

  document.addEventListener("paste", function(e) {
    if (_intercept) {
      _intercept = false;
      e.preventDefault();
      _resolve(e.clipboardData.getData(_dataType));
    }
  });

  return function(dataType) {
    return new Promise(function(resolve, reject) {
      _intercept = true; // Race condition?
      _resolve = resolve;
      _dataType = dataType || "text/plain";
      try {
        if (!document.execCommand("paste")) {
          _intercept = false;
          reject(new Error("Unable to paste. Perhaps it's not available in your browser?"));
        }
      } catch (e) {
        _intercept = false;
        reject(new Error(e));
      }
    });
  };
}());

// Handle IE behaviour.
if (typeof ClipboardEvent === "undefined" &&
    typeof window.clipboardData !== "undefined" &&
    typeof window.clipboardData.setData !== "undefined") {

  /*! promise-polyfill 2.0.1 */
  !function(a){function b(a,b){return function(){a.apply(b,arguments)}}function c(a){if("object"!=typeof this)throw new TypeError("Promises must be constructed via new");if("function"!=typeof a)throw new TypeError("not a function");this._state=null,this._value=null,this._deferreds=[],i(a,b(e,this),b(f,this))}function d(a){var b=this;return null===this._state?void this._deferreds.push(a):void j(function(){var c=b._state?a.onFulfilled:a.onRejected;if(null===c)return void(b._state?a.resolve:a.reject)(b._value);var d;try{d=c(b._value)}catch(e){return void a.reject(e)}a.resolve(d)})}function e(a){try{if(a===this)throw new TypeError("A promise cannot be resolved with itself.");if(a&&("object"==typeof a||"function"==typeof a)){var c=a.then;if("function"==typeof c)return void i(b(c,a),b(e,this),b(f,this))}this._state=!0,this._value=a,g.call(this)}catch(d){f.call(this,d)}}function f(a){this._state=!1,this._value=a,g.call(this)}function g(){for(var a=0,b=this._deferreds.length;b>a;a++)d.call(this,this._deferreds[a]);this._deferreds=null}function h(a,b,c,d){this.onFulfilled="function"==typeof a?a:null,this.onRejected="function"==typeof b?b:null,this.resolve=c,this.reject=d}function i(a,b,c){var d=!1;try{a(function(a){d||(d=!0,b(a))},function(a){d||(d=!0,c(a))})}catch(e){if(d)return;d=!0,c(e)}}var j=c.immediateFn||"function"==typeof setImmediate&&setImmediate||function(a){setTimeout(a,1)},k=Array.isArray||function(a){return"[object Array]"===Object.prototype.toString.call(a)};c.prototype["catch"]=function(a){return this.then(null,a)},c.prototype.then=function(a,b){var e=this;return new c(function(c,f){d.call(e,new h(a,b,c,f))})},c.all=function(){var a=Array.prototype.slice.call(1===arguments.length&&k(arguments[0])?arguments[0]:arguments);return new c(function(b,c){function d(f,g){try{if(g&&("object"==typeof g||"function"==typeof g)){var h=g.then;if("function"==typeof h)return void h.call(g,function(a){d(f,a)},c)}a[f]=g,0===--e&&b(a)}catch(i){c(i)}}if(0===a.length)return b([]);for(var e=a.length,f=0;f<a.length;f++)d(f,a[f])})},c.resolve=function(a){return a&&"object"==typeof a&&a.constructor===c?a:new c(function(b){b(a)})},c.reject=function(a){return new c(function(b,c){c(a)})},c.race=function(a){return new c(function(b,c){for(var d=0,e=a.length;e>d;d++)a[d].then(b,c)})},"undefined"!=typeof module&&module.exports?module.exports=c:a.Promise||(a.Promise=c)}(this);

  clipboard.copy = function(data) {
    return new Promise(function(resolve, reject) {
      // IE supports string and URL types: https://msdn.microsoft.com/en-us/library/ms536744(v=vs.85).aspx ... We only support the string type for now.
      if (typeof data !== "string" && !("text/plain" in data)) {
        throw new Error("You must provide a text/plain type.")
      }
      var strData = (typeof data === "string" ? data : data["text/plain"]);
      var copySucceeded = window.clipboardData.setData("Text", strData);
      copySucceeded ? resolve() : reject(new Error("Copying was rejected."));
    });
  }
  clipboard.paste = function(data) {
    return new Promise(function(resolve, reject) {
      var strData = window.clipboardData.getData("Text");
      if (strData) {
        resolve(strData);
      } else {        // The user rejected the paste request.
        reject(new Error("Pasting was rejected."));
      }
    });
  }
}
//<!-- clipboard: end -->


</script>
<form name="form">
<!-- for captions: end -->\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
__EOF1__
}






print qq[<center><p align=center><FONT face=arial SIZE=6><B>];
if ($GENERATE) {
        print qq[$TITLE]
} else {
        if ($STUPID_UNUSED_FLAG==0) { print "Compact"; }
        my $CWD2=$CWD; 
		#####why was i adding spaces? so it wouldn't word wrap, right? How about we just make the font smaller on the next line?
		#$CWD2 =~ s/([\\\/])/$1 /g;
        print qq[$RECURSIVE4PRINT Index Of <font size=2>$CWD2</font>];
}
print qq[</B></font></p></center><BR><BR>\n<p align="center">\n\n\n\n\n\n\n\n];





############ PROCESS EACH IMAGE:
my $currentLineCount = 0;
my @FILES=();
while ($line=<STDIN>) {
    chop $line;
    $currentLineCount++;
	push(@FILES,$line);
    if ($currentLineCount == $N) { last; }
}
if ($DEBUG_TAGREAD) {
	foreach my $file (@FILES) { print "<p align=left>Detected file: $file<BR>\n";}
	print "**** TAGFILENAME IS $TAGFILE_NAME   <BR>\n";
}


if (-e $TAGFILE_NAME) {
	if ($DEBUG_TAGREAD) { my $abs_path = File::Spec->rel2abs($TAGFILE_NAME);	print "Tagfile is $abs_path...<BR>\n"; }
	$TAGMODE=1;
	$resize_x -= $WIDTH_DECREASE_FOR_TAGMODE;	#give more room for tags on right
	$resize_y -= $HEIGHT_DECREASE_FOR_TAGMODE;	#give more room for tags on right
	&read_tags(\@FILES);
	if ($DEBUG_TAGREAD) {
		foreach my $key (keys %tags) { print "Detected key: $key   <BR>\n";}
		foreach my $key (keys %tags) {	print " ===> \%tags{".$key."}. = \"".$tags{$key}."\"   <BR>\n"; }
	}



if ($CREATE_CAPTIONS) { 
	print qq[\n\n\n\n\n\n\n\n
<!-- captions: begin -->
<BR><BR><font size=5><B>BACKSTORY:</B></font><p align="center">
        <table id="Lexington" align=center border=0 cellspacing=0 cellpadding=0>
		<tr>
			<td align="center">
				<input    name="caption" id="inputTextToSave_backstory1" type="hidden" value=":postcaption-">
				<textarea name="caption" id="inputTextToSave_backstory2" style="width: $DEFAULT_BACKSTORY_TEXTAREA_WIDTH; height: $DEFAULT_BACKSTORY_TEXTAREA_HEIGHT" onkeyup="captionkeyup(event)">$DEFAULT_BACKSTORY_TEXT</textarea>
			</td>
		</tr>	
		</table>
<!-- captions: end -->\n\n\n\n\n\n\n\n
	\n];
}




#	print "<BR><BR><font size=5><B>GLOBAL TAGS:</B></font><P>\n";
	print "<BR><BR><font size=5><B>GLOBAL TAGS:</B></font><P align=\"center\">\n";
	foreach my $tmptag (sort keys %globaltags) {
		$tmptag = &censor_tag($tmptag);
		$tmptag =~ s/_SPA*CE*_/ /g;
		$tmptag =~ s/_ENTE*R*_/\n/g;
		print $tmptag . "<BR>\n";
	}
	print "<BR>\n\n\n\n\n\n\n\n\n\n";
} else {
	$TAGMODE=0;
}
#OLD:
#while ($line=<STDIN>) 
    #chop $line;
    #$currentLineCount++;
    #$filename = $line;
#NEW:
my $currentFile=0;
my $totalFiles=@FILES;
foreach $filename (@FILES) {
	$currentFile++;
	#if ($filename =~ /\//) { $filename =~ s/\//\\/g; }
    if ($filename =~ /^[0-9\s][0-9\s]-[0-9\s][0-9\s]-[0-9\s][0-9\s]\s+[0-9\s][0-9\s]:[0-9\s][0-9\s]\s+[0-9,]*\s/) {
        #print "Scrub: $filename\n";
        ($nothing,$date,$time,$size,$tmpname)=split(/\s+/,"$line");
        $filename = $tmpname;
    }
	if (!-e $filename) { 
		print "\n\n\n\n\n\n\n\n\n\n\n\n\n<!-- skipping $filename because it does not exist -->\n";
		print 007;
		next; 
	}
	if (   ($filename !~ /\.jpe?g$/i)
		&& ($filename !~ /\.gif$/i)
		&& ($filename !~ /\.png$/i)	
		&& ($filename !~ /\.bmp$/i)
		&& ($filename !~ /\.ico$/i)
		&& ($filename !~ /\.tiff?$/i)
		&& ($filename !~ /\.pcx$/i)
		&& ($filename !~ /\.art$/i)
		&& ($filename !~ /\.cb[rz]$/i)
		&& ($filename !~ /\.tnb$/i)
		&& ($filename !~ /\.mkv$/i)						#201510
		&& ($filename !~ /\.avi$/i)						#20080424 added in response to FlickR now allowing video
		&& ($filename !~ /\.mp4$/i)						#20080424 added in response to FlickR now allowing video
		&& ($filename !~ /\.flv$/i)						#20080424 added in response to FlickR now allowing video
		&& ($filename !~ /\.mov$/i)						#20080424 added in response to FlickR now allowing video
		&& ($filename !~ /\.wmv$/i)						#201012
		&& ($filename !~ /\.mpe?g$/i)					#20080424 added in response to FlickR now allowing video
		&& ($filename !~ /\.vob$/i)						#201510\
		&& ($filename !~ /\.bdmv$/i)					#201510 \
		&& ($filename !~ /\.ts$/i)						#201510  \___ Updated from %FILEMASK_IMAGE%
		&& ($filename !~ /\.m2ts$/i)					#201510  /        and from %FILEMASK_VIDEO% 
		&& ($filename !~ /\.rm$/i)						#201510 /            environment variables.
		&& ($filename !~ /\.qt$/i)						#201510/
		&& ($filename !~ /\.asf$/i)						#201510
		&& ($filename !~ /\.asx$/i)						#201510
		&& ($filename !~ /\.fli$/i)						#201510
		&& ($filename !~ /\.swf$/i)						#201510
		&& ($filename !~ /\.m4v$/i)						#201510
		&& ($filename !~ /\.webm$/i)					#201510
		) 
			{
				print "\n<!-- skipping $filename because its extension is not an image -->\n";
				next;
			};

	my $isVideo=0;
    if ($filename =~ /\.asf$/i)     { $isVideo=1; }
    if ($filename =~ /\.avi$/i)     { $isVideo=1; }
    if ($filename =~ /\.ts$/i)      { $isVideo=1; }

	##### 20060822 WTF -- I find this, but it's still like this?!?!: --- 2015 - too bad my documentation standards were lower 10 years ago!
#bad idea: lename =~ /\.idx$/i)     { $isVideo=1; } #20051010 let's try this
    if ($filename =~ /\.idx$/i)     { $isVideo=1; } #excluded from some things later
#bad idea: lename =~ /\.idx$/i)     { $isVideo=1; } #20051010 let's try this
#bad idea: lename =~ /\.sub$/i)     { $isVideo=1; } #20051010 let's try this
    if ($filename =~ /\.sub$/i)     { $isVideo=1; } #excluded from some things later
    if ($filename =~ /\.srt$/i)     { $isVideo=1; } #excluded from some things later
#bad idea: lename =~ /\.sub$/i)     { $isVideo=1; } #20051010 let's try this
	if ($filename =~ /\.flv$/i)     { $isVideo=1; }
    if ($filename =~ /\.mkv$/i)     { $isVideo=1; }
    if ($filename =~ /\.mov$/i)     { $isVideo=1; }
    if ($filename =~ /\.mpa$/i)     { $isVideo=1; } #may actually be audio (?)
    if ($filename =~ /\.mp4$/i)     { $isVideo=1; } #may actually be audio... but we'll go with video.
    if ($filename =~ /\.mpe?g?$/i)  { $isVideo=1; }
#   if ($filename =~ /\.nfo$/i)     { $isVideo=1; }  #Not really a video, but a frequent companion file
    if ($filename =~ /\.ogm/i)	    { $isVideo=1; }
    if ($filename =~ /\.ra?m$/i)    { $isVideo=1; }
    if ($filename =~ /\.swf$/i)     { $isVideo=1; }
#   if ($filename =~ /\.txt$/i)     { $isVideo=1; } #cheating.. a lot of my isvideo logic really should apply to ismedia or something
    if ($filename =~ /\.wmv$/i)     { $isVideo=1; }
    if ($filename =~ /\.viv$/i)     { $isVideo=1; }
    if ($filename =~ /\.vob$/i)     { $isVideo=1; }  
    if ($filename =~ /\.webm$/i)    { $isVideo=1; }  
#   if ($filename =~ /\.zip$/i)     { $isVideo=1; } #cheating

    if ($STUPID_UNUSED_FLAG) {
        $line = qq[
        <table id="Brooklyn" align=center border=0 cellspacing=0 cellpadding=0>
        <TR valign=middle>
        <TD align=center];
		$line .= qq[><font size=5 face=arial><B>];
		my $linkfilename = "$CWD$filename";
		$linkfilenameConverted = &convert_filename_to_link($linkfilename);
		#if ($isVideo) { $line .= qq[<a href="$linkfilename" target="$currentLineCount">]; }
		if ($isVideo) { $line .= qq[<a href="$linkfilenameConverted" target="$currentLineCount">]; }	#201511
		$line .= $filename;
		if ($isVideo) { $line .= qq[</a>]; }
		$line .= qq[</b><font><BR>\n];
    } else {
        $line = "";
    }



	my $filenameRegex = &convert_filename_to_regex($filename);


	##### Figure out options that only apply if we are not showing thumbnails:
	#print "usgimglib is $USEIMGLIB\n";	#0
	if ($USEIMGLIB==1) {
		($x, $y) = &imgsize($filename);
		#print "x is $x, y is %y";

		$resize_x_tmp="";		if ($x > $y) { $resize_x_tmp=$resize_x; }
		$resize_y_tmp="";		if ($y > $x) { $resize_y_tmp=$resize_y; }																if ($verbose) { print "Checking to see if x=$x > resize_x_tmp=$resize_x_tmp [resize_x=$resize_x} or if y=$y > resize_y_tmp=$resize_y_tmp [resize_y=$resize_y]<BR>\n"; }

		#$verbose=1;#

		##### Get the size of image:
		#DEBUG: print "(\$x, \$y) = &imgsize(\"$real\");
			if ((($x > $resize_x_tmp) && ($resize_x_tmp>0)) || (($y > $resize_y_tmp) && ($resize_y_tmp>0))) {
			if ($verbose) { print "Image needs to be resized...<BR>\n"; }
			if (($x > $resize_x_tmp) && ($resize_x_tmp > 0)) {													if ($verbose) { print "x of $x indeed bigger than resize_x of $resize_x_tmp<BR>\n"; }
				$resize_x_or_zero = $resize_x_tmp;
				$ratio = $resize_x_tmp / $x;
				$resize_y_or_zero = &round($ratio * $y);														if ($verbose) { print "ratio is $ratio ... resize_y is now $resize_y_or_zero .. resize_x / x = $resize_x_tmp / $x<BR>"; }
			}#endif
			if ((($resize_y_or_zero > $resize_y_tmp) || ($y > $resize_y_tmp)) && ($resize_y_tmp > 0)) {			if ($verbose) { print "Either y of $y or Resize_y_or_zero of $resize_y_or_zero is indeed bigger than resize_y of $resize_y_tmp<BR>\n"; }
				$resize_y_or_zero = $resize_y_tmp;
				$ratio = $resize_y_tmp / $y;
				$resize_x_or_zero = &round($ratio * $x);														if ($verbose) { print "resize_x is now $resize_x_or_zero .. ratio is $ratio.. resize_y / y = $resize_y_tmp / $y<BR>"; }
			}#endif	
																												if ($verbose) { print "Final dimensions are $resize_x_or_zero x $resize_y_or_zero<BR>\n"; }
		} else {																								if ($verbose) { print "Image size is okay...<BR>\n"; }
			$resize_x_or_zero = 0;	
			$resize_y_or_zero = 0;
		}#endif
		if ($verbose) { print "x=$x,resize_x=$resize_x,resize_x_tmp=$resize_x_tmp,y=$y,resize_y=$resize_y,resize_y_tmp=$resize_y_tmp,resize_x_or_0/resize_y_or_0=$resize_x_or_zero/$resize_y_or_zero<BR>\n"; }
		$WIDTH="";	$HEIGHT="";
		#DEBUG: print "tagmode is $TAGMODE\n";
		if (($resize_x_or_zero) && ($resize_x_tmp > 0)) { 
			$tmpdimension = $resize_x_tmp-$MARGIN_X;
			if ($TAGMODE) { $tmpdimension -= $WIDTH_DECREASE_FOR_TAGMODE; }
			$WIDTH ="  width=\"" . $tmpdimension . "\" "; 
		}
		if (($resize_y_or_zero) && ($resize_y_tmp > 0)) { 
			$tmpdimension = $resize_y_tmp-$MARGIN_Y;
			$HEIGHT=" height=\"" . $tmpdimension . "\" "; 
		}
	}#endif $USEIMGLIB


	##### PRINT OUT THE <IMG> TAG, WITH AN <A> TAG AROUND IT, IF SPECIFIED:
	if ($IMAGES_LINK_TO_THEMSELVES==1) { 
		#$href = $CWD . &URLEncode($filename);	#3/18/2007: amazingly, taking this out makes it work much better in IE on XP 
		#$href = $CWD . $filename;
		 $href = $CWD . &URLEncode($filename);	#201511: bringinb ack original behavior again:
		$line .= qq[<a target="_$$] . $target++ .qq[" href="$href">]; 
	}

	### block moved to above

	if ($isVideo==0) {

		#2000-201510 value was "$CWD$filename", but GENERATE filename has always just been "$filename":
		$srcToUse = $linkfilenameConverted;				if ($GENERATE)	{ $srcToUse="$filename"; } 

		$line .= "\n\t\t\t<img $WIDTH $HEIGHT border=0 alt=\"$filename\" src=\"$srcToUse\"  border=0><BR>\n";

		#my $srcToUse2=$srcToUse;			$srcToUse2 =~ s/\%20/ /g;
		#line .= "\n\t\t\t<img $WIDTH $HEIGHT border=0 alt=\"$filename\" src=\"$srcToUse2\" border=0><BR>\n";			#experimental #

	} else {							#IE only
		my $VIDEO_WIDTH_MINIMUM=220;
		my $VIDEO_HEIGHT_MINIMUM=220;
		my $VIDEO_WIDTH=440;
		my $VIDEO_HEIGHT=440;

		if (!$SUPPRESS_HTML4_VIDEO_EMBED_WE_USE_FOR_IE) {
			$line .= qq[\n
				<!-- HTML4 20000 embed method: -->
				<object id="Player" width="$VIDEO_WIDTH" height="$VIDEO_HEIGHT" quality="best" CLASSID="CLSID:6BF52A52-394A-11d3-B153-00C04F79FAA6">
				  <param name="URL" value="$CWD$filename"><!-- fileName also works instead of URL, which is weird -->
				  <param name="autoStart" value="false">
					<!-- <embed type="application/x-mplayer2" pluginspage="http://www.microsoft.com/Windows/MediaPlayer/" src="$CWD$filename" name="MediaPlayer1" width=280 height=256 autostart=1 showcontrols=1 volume=-450> -->
				</object><BR>
			\n];
		}

		#Chrome:
		$line .= qq[\n
			<!-- HTML5 2015 embed method: -->
			<video controls height="400" width="$CHROME_VIDEO_WIDTH">
				<source src="$CWD$filename">
				Your browser does not support the video tag.
			</video>
		\n];
	}



	if ($IMAGES_LINK_TO_THEMSELVES==1) { $line .= "</a>"; }

	$line .= "<BR>\n";											#20080403 - added <BR> to this line
	if ($STUPID_UNUSED_FLAG) {
        $line .= qq[        </TD>\n];
		#line .= qq[        </TR>\n];
		##### IF WE HAVE A TAGFILE, THEN WE WILL DISPLAY THE TAGS
		##### IN A TABLE NEXT TO THE IMAGE.   THIS WAS HARD!
		if ($USECLIOLIB && $TAGMODE) {
			@tmptags = split(/,/,"$tags{$filename}");
			#line .= qq[       <TR>];
			$line .= qq[       <TD align=left>\n       <TABLE>\n];

			##### DISPLAY THE TAGS WITH THIS LOOP:
			@YouTubeTags=();
			@FlickrTags=();
			foreach $tmptag (sort @tmptags) {
				if ($globaltags{$tmptag} ne "") { next; }
				#DEBUG: print "\$globaltags{".$tmptag."}==\"".$globaltags{$tmptag}."\"";
				$tmptag = &censor_tag($tmptag);
				$tmptag =~ s/_SPA*CE*_/ /g;
				$line .= "\t\t<TR valign=middle>" . 
						 "<TD align=left><font face=Arial size=3><nobr>" . 
						  $tmptag . "</nobr></font></TD>\n";
				push(@FlickrTags,"\"$tmptag\"");	#tags need quotes around them for flickr, in case they have spaces
				$tmptag =~ s/ //g;					#spaces are invalid for YouTube tags
				push(@YouTubeTags,$tmptag);
			}
			$line .= qq[        </TR>\n];
			$line .= qq[        </TABLE><!-- 1 -->\n];
			$line .= qq[        </TD>\n];
			$line .= qq[        </TR>\n];

			if ($CREATE_CAPTIONS) {
				$line .= qq[
		<!-- caption begin -->
		<tr>
			<td align="center">
				<input type="hidden" name="caption" value="$filenameRegex:caption-">
				<textarea name="caption" id="inputTextToSave_$currentFile" style="width: $DEFAULT_CAPTION_TEXTAREA_WIDTH; height: $DEFAULT_CAPTION_TEXTAREA_HEIGHT" onkeyup="captionkeyup(event)"
				 todo="if we decide it looks good later, make width be same or 85% of image width rather than hardcoded"></textarea>
			</td>
			<td></td>
		</tr>
		<!-- caption end -->
					     \n];
			}

			$line .= qq[        
			<TR valign="top"><TD align="center"><button id="button1" onclick="CopyToClipboard('div$currentFile'); return false;">caption => clipboard</button></TD></TR>
            <TR><TD align=center>];
			$tmp = "";
			if ($isVideo) {		#show the tags again in a cut-and-paste style suitable for youtube and flickr
				foreach my $tmptag (sort keys %globaltags) { 
					$tmptag = &censor_tag($tmptag);
					$tmptag =~ s/_SPA*CE*_/ /g;
					$tmptag =~ s/_ENTE*R*_/\n/g;
					push(@FlickrTags,"\"$tmptag\"");
					$tmptag =~ s/ //isg;
					push(@YouTubeTags,"$tmptag");
				}
				$tmp .= "<B>";	#YouTube Tags:<BR>";
				$tmp .= join(", ",@YouTubeTags);
				$tmp .= "</B><P>";
				$tmp .= "<B>";	#FlickR Tags:<BR>";
				$tmp .= join(" ",@FlickrTags);
				$tmp .= "</B><P>";
			}
			$tmp .=  &censor_caption($captions{$filename});
			$tmp .= &sponsor_caption($filename);
			if ($postcaptionsFromTagfile{$filename} ne "") { $tmp .= "<BR><BR><BR>" . &linkify($postcaptionsFromTagfile{$filename}); }

			$tmp =~ s/_ENTER_/<BR>/g;
			$tmp =~ s/_ENT_/<BR>/g;
			$tmp =~ s/_SPACE_/ /g;			#this never happens, but it's nice to be thorough
			$tmp =~ s/_SPC_/ /g;			#this never happens, but it's nice to be thorough
			$tmp =~ s/\n/<BR>/g;			#makeimg is for webpage generation usually! 
			$tmp =~ s/\\"/"/g;
			$line .= qq[			<div id="div$currentFile">$tmp</a>];
			$line .= qq[        </TD></TR>
			<TR valign="top"><TD align="center"><button id="button1" onclick="CopyToClipboard('div$currentFile'); return false;">caption => clipboard</button></TD></TR>
];

		}
        $line .= qq[        </TABLE><!-- 2 --><BR><BR><BR>];

		$line .= qq[\n\n\n\n\n\n\n\n\n<!-- *************** Picture $currentFile of $totalFiles *************** -->\n\n\n\n\n\n\n\n\n\n];


    }







	##### NOW THAT WE'RE DONE FIGURING IT ALL OUT,
	##### SPIT IT OUT!:
    print $line; $line="";
    if ($currentLineCount == $N) { 
		#2015 try not exiting (can't break because strict subs): exit;
	}
}


	if ($CREATE_CAPTIONS) {
		$line .= qq[\n\n\n\n\n\n\n\n
<!-- for captions: begin -->
<table border=0 align="center">
	<tr><td align="center"><font size=5><B>ASSEMBLED CAPTIONS:</B></font></td></tr>
	<tr>
		<td align="center">
			<!-- <textarea id="allTextOLD" style="width:512px;height:256px"></textarea> -->
			<p id="allText" onload="assembleAllText();" style="font-family: monospace; font-size: $CAPTION_PREVIEW_FONT_SIZE;"></p>
		</td>
	</tr>
	<tr>
		<td align="center">
			<input  type="hidden" id="inputFileNameToSaveAs" value="$CAPTION_SAVE_FILENAME"></input>
			<button type="button" id="inputFileButtonToSave" class="btn" onclick="saveTextAsFile()">$CAPTION_SAVE_BUTTON_TEXT</button>
		</td>
	</tr>
</table>
</form>
<script type='text/javascript'>
			assembleAllText();		//do this after the page is done loading, haha
</script>
<!-- for captions: end -->];
	}
    print $line; $line="";



## DONE!
































########################################################
sub round {
	my($number) = shift;
	return int($number + .5 * ($number <=> 0));
}#endsub
########################################################



########################################################
sub convert_filename_to_link {
	my $s = $_[0];
#	$s =~ s/[A-Z]://g;	#remove drive letter ... this should maybe be a configurable option
	$s = "file:///$s";
	$s =~ s/\\/\//g;
	$s =~ s/#/%23/g;	#change # to %20 
	$s =~ s/ /%20/g;	#change   to %20 ... this should maybe be a configurable option            #as of 2015, doing this for local images actually breaks IE - they c hanged their mind! ridiculous!
	$s =~ s/(file:\/\/\/)\//$1/g;
	return ($s);


	#PRE-2015 ways things looked, with %20s that don't work anymore: 
	#file:///C:/pics/New%20Pictures/2010_03_21_Vicky%20&%20Ryan%27s%20wedding/3%20-%20nature%20trail/20100320%20-%20Vicky%20&%20Ryan%27s%20wedding%20-%20post-ceremony%20-%200%20-%20nature%20trail%20-%20bald%20eagles%20-%20GEDC1757.jpg

	#201510: This type is the type that works for long long filenames:
	#file:///media/newPics/2013_08_02-2013_08_04_BronyCon/2013_08_04_1-flickr/hold/20130804 1945 - BronyCon - day 3 - after-math - Carolyn & the awesome singing girl - 194534.jpg" border=0></a><BR>

}#endsub
########################################################
