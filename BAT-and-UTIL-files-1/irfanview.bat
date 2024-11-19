@on break cancel
@echo off

set IRFANVIEW="%UTIL2%\IRFANVIEWPORTABLE\App\IrfanView64\i_view64.exe"
call validate-environment-variable IRFANVIEW

      start %IRFANVIEW %*
 echo start %IRFANVIEW %*
:           %IRFANVIEW %*
:echo       %IRFANVIEW %*
 
  :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   ::: 
  :::  
  ::: See the file "i_options.txt" (IrfanView folder) for the most recent version on all command line options.
  :::  
  ::: Command line options allow you to set some functions of IrfanView before the viewer is launched.
  :::  
  ::: These command line options are supported in IrfanView:
  :::  
  ::: /one -        force 'Only one instance' 
  ::: /fs -        force Full Screen display 
  ::: /bf -        force 'Fit images to desktop' display option 
  ::: /title=text -        set window title to 'text' 
  ::: /pos=(x,y) -        move the window to x,y 
  ::: /convert=filename -        convert input file to 'filename' and CLOSE IrfanView  
  :::           (see Pattern page for additional filename options)
  ::: /slideshow=txtfile -        play slideshow with the files from 'txtfile' 
  ::: /slideshow=folder -        play slideshow with the files from 'folder' 
  ::: /reloadonloop -        reload input source used in /slideshow when list finished 
  ::: /filelist=txtfile -        use filenames from "txtfile" as input, see examples below 
  ::: /thumbs -        force thumbnails 
  ::: /killmesoftly -        close all IrfanView instances (exit after command line) 
  ::: /cmdexit -        close current IrfanView after command line processing 
  ::: /closeslideshow -        close slideshow and close IrfanView after the last image 
  ::: /page=X -        open page number X from a multipage input image 
  ::: /crop=(x,y,w,h) -        crop input image: x-start, y-start, width, height 
  ::: /print -        print input image to default printer and close IrfanView 
  ::: /print="Name" -        print input image to specific printer and close IrfanView 
  ::: /resize=(w,h) -        resize input image to w (width) and h (height) 
  ::: /resize_long=X -        resize input image: set long side to X 
  ::: /resize_short=X -        resize input image: set short side to X 
  ::: /resample -        for resize: use Resample option (better quality) 
  ::: /capture=X -        capture the screen or window (see examples below) 
  ::: /ini -        use the Windows folder for INI/LST files (read/save) 
  ::: /ini="Folder" -        use the folder "Folder" for INI/LST files (read/save) 
  ::: /clippaste -        paste image from the clipboard 
  ::: /clipcopy -        copy image to the clipboard 
  ::: /silent -        don't show error messages for command line read/save errors 
  ::: /invert -        invert the input image (negative) 
  ::: /dpi=(x,y) -        change DPI values, set DPIs for scanning 
  ::: /scan -        acquire the image from the TWAIN device - show TWAIN dialog 
  ::: /scanhidden -        acquire the image from the TWAIN device - hide TWAIN dialog 
  ::: /batchscan=(options) -        simulate menu: File->Batch Scanning, see examples below 
  ::: /bpp=BitsPerPixel -        change color depth of the input image to BitsPerPixel 
  ::: /swap_bw -        swap black and white color 
  ::: /gray -        convert input image to grayscale 
  ::: /rotate_r -        rotate input image to right 
  ::: /rotate_l -        rotate input image to left 
  ::: /hflip -        horizontal flip 
  ::: /vflip -        vertical flip 
  ::: /filepattern="x" -        browse only specific files 
  ::: /sharpen=X -        open image and apply the sharpen filter value X 
  ::: /effect=(X,p1,p2) -        apply effect filter X, see below for examples 
  ::: /contrast=X -        open image and apply the contrast value X 
  ::: /bright=X -        open image and apply the brighntess value X 
  ::: /gamma=X -        open image and apply the gamma correction value X 
  ::: /advancedbatch -        apply Advanced Batch Dialog options to image (from INI file) 
  ::: /hide=X -        hide toolbar, status bar, menu and/or caption of the main window (see examples below) 
  ::: /transpcolor=(r,g,b) -        set transparent color if saving as GIF/PNG/ICO 
  ::: /aspectratio -        used for /resize and /resample, keep image proportions 
  ::: /info=txtfile -        write image infos to "txtfile" 
  ::: /fullinfo -        used for /info, write EXIF, IPTC and Comment data 
  ::: /append=tiffile -        append image as (TIF) page to "tiffile" 
  ::: /multitif=(tif,files) -        create multipage TIF from input files 
  ::: /panorama=(X,files) -        create panorama image from input files; X = direction (1 or 2) 
  ::: /jpgq=X -        set JPG save quality 
  ::: /tifc=X -        set TIF save compression 
  ::: /wall=X -        set image as wallpaper; see below for /random and examples 
  ::: /extract=(folder,ext) -        extract all pages from a multipage file 
  ::: /import_pal=palfile -        import and apply a special palette to the image (PAL format) 
  ::: /export_pal=palfile -        export image palette to file (PAL format) 
  ::: /jpg_rotate=(options) -        JPG lossless rotation, see examples below 
  ::: /monitor=X -        start EXE-Slideshow on monitor X  
  ::: /window=(x,y,w,h) -        set EXE-Slideshow window position and size 
  :::  
  :::  
  ::: Notes:
  :::  
  ::: - Only lower case options are supported (don't type any UPPERCASE letters) !
  ::: - Input file name (if required) is always the first parameter!
  ::: - Use "" for file names with spaces, example: "c:\images\dummy test file.jpg".
  ::: - Write always the FULL paths for file names (incl. drive letter).
  ::: - You can combine several options in one command.
  ::: - Wildcards (*) supported only for /convert, /print, /info and /jpg_rotate.
  ::: - Maximal command line length is limited by Windows, so use shorter names/paths.
  ::: - Most settings are loaded from the INI file. Using prepared INIs and /ini=folder option, you can extend the possibilities.
  ::: - IrfanView exit code is 0. If /convert or /print is used, there is 1 or 2 also possible, for load/save errors.
  :::  
  :::  
  ::: Example for conversion:
  :::  
  ::: i_view32.exe c:\test.bmp /convert=c:\test.jpg
  ::: Convert file: 'c:\test.bmp' to 'c:\test.jpg' without GUI.
  :::  
  ::: i_view32.exe c:\*.jpg /convert=d:\temp\*.gif
  ::: i_view32.exe c:\*.jpg /resize=(500,300) /convert=d:\temp\*.png
  ::: i_view32.exe c:\*.jpg /resize=(500,300) /aspectratio /resample /convert=d:\temp\*.png
  ::: i_view32.exe /filelist=c:\mypics.txt /resize=(500,300) /aspectratio /resample /convert=d:\temp\*.png
  ::: i_view32.exe c:\test.bmp /convert=c:\test_$Wx$H.jpg
  ::: i_view32.exe c:\test.bmp /resize=(100,100) /resample /aspectratio /convert=d:\$N_thumb.jpg
  ::: i_view32.exe c:\test.bmp aspectratio /convert=d:\temp\$T(%Y%m%d)\test_$Wx$H.jpg
  ::: i_view32.exe c:\test.bmp /convert=$D$N.jpg
  ::: i_view32.exe c:\*.bmp /convert=$D$N.jpg
  ::: i_view32.exe c:\*.jpg /advancedbatch /convert=c:\temp\*.jpg
  ::: i_view32.exe c:\test.bmp /transpcolor=(255,255,255) /convert=c:\giftest.gif
  ::: (Note: Supported are all IrfanView read/save formats except audio/video.) 
  :::  
  ::: Example for slideshow:
  :::  
  ::: i_view32.exe /slideshow=c:\mypics.txt
  ::: (Note: The file 'c:\mypics.txt' contains, in each line, a name of an image, including the full path OR path relative to "i_view32.exe".) 
  :::  
  ::: i_view32.exe /slideshow=c:\mypics.txt /reloadonloop
  ::: i_view32.exe /slideshow=c:\images\
  ::: i_view32.exe /slideshow=c:\images\ /reloadonloop
  ::: i_view32.exe /slideshow=c:\images\*.jpg
  ::: i_view32.exe /slideshow=c:\images\test*.jpg
  ::: You have to close IrfanView after the last image from the TXT file, if not /closeslideshow is used.
  :::  
  ::: Example for /closeslideshow:
  :::  
  ::: i_view32.exe /slideshow=c:\mypics.txt /closeslideshow
  ::: IrfanView will be closed after the last image from 'c:\mypics.txt'.
  :::  
  ::: Example for thumbnails:
  :::  
  ::: i_view32.exe c:\test\image1.jpg /thumbs
  ::: Open 'image1.jpg' and display thumbnails from directory 'c:\test'.
  :::  
  ::: i_view32.exe c:\test\ /thumbs
  ::: Display thumbnails from directory 'c:\test'.
  :::  
  ::: i_view32.exe /filelist=c:\mypics.txt /thumbs
  ::: Load filenames from TXT file and display as thumbnails.
  :::  
  ::: Example for filelist:
  :::  
  ::: i_view32.exe /filelist=c:\mypics.txt
  ::: i_view32.exe /filelist=c:\mypics.txt /convert=d:\test\*.jpg
  ::: i_view32.exe /filelist=c:\mypics.txt /thumbs
  :::  
  ::: Example for close:
  :::  
  ::: i_view32.exe /killmesoftly
  ::: Close IrfanView and terminate all instances.
  :::  
  ::: Example for /page:
  :::  
  ::: i_view32.exe c:\test.tif /page=3
  ::: Open page number 3 from the multipage image 'c:\test.tif'.
  :::  
  ::: Example for /crop:
  :::  
  ::: i_view32.exe c:\test.jpg /crop=(10,10,300,300)
  ::: i_view32.exe c:\test.jpg /crop=(10,10,300,300) /convert=c:\giftest.gif
  ::: Open 'c:\test.jpg' and crop: x-start=10, y-start=10, width=300, height=300 (in pixels).
  :::  
  ::: Example for /print:
  :::  
  ::: i_view32.exe c:\test.jpg /print
  ::: Open 'c:\test.jpg', print the image to default printer and close IrfanView.
  :::  
  ::: i_view32.exe c:\test.jpg /print="Printer Name"
  ::: Open 'c:\test.jpg', print the image to specific printer and close IrfanView.
  :::  
  ::: i_view32.exe c:\*.jpg /print
  ::: Print all JPGs from "C:\" and close IrfanView.
  :::  
  ::: Note: The actual settings from the INI file are used.
  :::  
  ::: Example for /resize:
  :::  
  ::: i_view32.exe c:\test.jpg /resize=(300,300) /resample
  ::: Open 'c:\test.jpg' and resample: width=300, height=300.
  ::: (Note: Resample uses the active resample filter from the INI file.)
  :::  
  ::: i_view32.exe c:\test.jpg /resize=(300,300) /aspectratio
  ::: Open 'c:\test.jpg' and resize: width= max. 300, height= max. 300, proportional.
  :::  
  ::: i_view32.exe c:\test.jpg /resize_long=300 /aspectratio /resample
  ::: Open 'c:\test.jpg' and resample: long side=300, short side=proportional.
  :::  
  ::: i_view32.exe c:\test.jpg /resize=(300,0)
  ::: Open 'c:\test.jpg' and resize: width=300, height=original.
  :::  
  ::: i_view32.exe c:\test.jpg /resize=(300,0) /aspectratio
  ::: Open 'c:\test.jpg' and resize: width=300, height=proportional.
  :::  
  ::: i_view32.exe c:\test.jpg /resize=(150p,150p)
  ::: Open 'c:\test.jpg' and resize: width=150%, height=150%.
  :::  
  ::: Example for /capture:
  :::  
  ::: i_view32.exe /capture=0
  ::: Capture the whole screen.
  ::: i_view32.exe /capture=6
  ::: Start in Capture mode, use last used capture dialog settings.
  :::  
  ::: capture values: 
  ::: 0 = whole screen 
  ::: 1 = current monitor, where mouse is located
  ::: 2 = foreground window
  ::: 3 = foreground window - client area
  ::: 4 = rectangle selection
  ::: 5 = object selected with the mouse
  ::: 6 = start in capture mode (can't be combined with other commandline options)
  :::  
  ::: Advanced examples:
  ::: i_view32.exe /capture=2 /convert=c:\test.jpg
  ::: Capture foreground window and save result as file.
  ::: i_view32.exe /capture=2 /convert=c:\capture_$U(%d%m%Y_%H%M%S).jpg
  ::: Capture foreground window and save result as file; the file name contains time stamp.
  :::  
  ::: Example for /ini:
  :::  
  ::: i_view32.exe /ini
  ::: i_view32.exe c:\test.jpg /ini
  ::: i_view32.exe c:\test.jpg /ini="c:\temp\"
  :::  
  ::: Example for /clippaste:
  :::  
  ::: i_view32.exe /clippaste
  ::: i_view32.exe /clippaste /convert=c:\test.gif
  :::  
  ::: Example for /clipcopy:
  :::  
  ::: i_view32.exe c:\test.jpg /clipcopy
  ::: i_view32.exe c:\test.jpg /clipcopy /killmesoftly
  :::  
  ::: Example for /invert:
  :::  
  ::: i_view32.exe c:\test.jpg /invert
  :::  
  ::: Example for /dpi:
  :::  
  ::: i_view32.exe c:\test.jpg /dpi=(72,72)
  :::  
  ::: Example for /scan:
  :::  
  ::: With the scan command, you can only combine: /print, /dpi, /gray and /convert. 
  ::: i_view32.exe /scan
  ::: i_view32.exe /scanhidden
  ::: i_view32.exe /scanhidden /dpi=(150,150)
  ::: i_view32.exe /scan /convert=c:\test.gif
  ::: i_view32.exe /scanhidden /gray /convert=c:\test.gif
  ::: i_view32.exe /print /scan
  :::  
  ::: Example for /batchscan=(options):
  :::  
  ::: options = all 8 options from the batch scanning dialog:
  ::: filename, index, increment, digits, skip, dest-folder, save-extension, multi-tif
  ::: i_view32.exe /batchscan=(scanfile,1,1,2,1,c:\temp,bmp,0)
  ::: i_view32.exe /batchscan=(scanfile,1,1,2,1,c:\temp,bmp,0) /dpi=(150,150)
  ::: i_view32.exe /batchscan=(scanfile,1,1,2,0,c:\temp,tif,1)
  ::: i_view32.exe /batchscan=("crazy, filename",1,1,2,0,"c:\temp\crazy, (folder)",tif,1)
  ::: i_view32.exe /batchscan=(scanfile,1,1,2,1,c:\temp,bmp,0) /scanhidden
  :::  
  ::: Example for /bpp:
  :::  
  ::: i_view32.exe c:\test.jpg /bpp=8
  ::: Open 'c:\test.jpg' and reduce to 256 colors. Supported BPP-values: 1, 4, 8 and 24 (decrease/increase color depth).
  :::  
  ::: Example for /filepattern:
  :::  
  ::: i_view32.exe c:\images\  /filepattern="*.jpg"
  ::: Go to folder "'c:\images" and load JPGs only in the browse/file list.
  :::  
  ::: i_view32.exe c:\images\ /thumbs /filepattern="*.jpg"
  ::: Go to folder "'c:\images" and show JPG thumbnails only.
  :::  
  ::: i_view32.exe c:\images\ /thumbs /filepattern="123*.jpg"
  ::: Go to folder "'c:\images" and show JPG with names "123*" as thumbnails.
  :::  
  ::: Example for /effect=(effect-nr,param1,param2)::
  :::  
  ::: i_view32.exe c:\test.jpg /effect=(6,3,0) 
  ::: Apply Median filter, parameter = 3.
  :::  
  ::: i_view32.exe c:\test.jpg /effect=(2,3,50) 
  ::: Apply Blur-2 filter, parameter1 = 3, parameter2 = 50.
  :::  
  ::: effect-nr values: (from Effect-Browser dialog): 
  ::: 1 = Blur
  ::: 2 = Blur-2
  ::: ...
  ::: 37 = Metallic Ice
  :::  
  ::: Example for /sharpen:
  :::  
  ::: i_view32.exe c:\test.jpg /sharpen=33
  :::  
  ::: Example for /hide:
  :::  
  ::: Values (can be combined (add values)):
  ::: Toolbar 1 
  ::: Status bar 2 
  ::: Menu bar 4 
  ::: Caption 8 
  ::: i_view32.exe c:\test.jpg /hide=1
  ::: Open 'c:\test.jpg', hide toolbar only.
  ::: i_view32.exe c:\test.jpg /hide=3
  ::: Open 'c:\test.jpg', hide toolbar and status bar.
  ::: i_view32.exe c:\test.jpg /hide=12
  ::: Open 'c:\test.jpg', hide caption and menu bar.
  ::: i_view32.exe c:\test.jpg /hide=15
  ::: Open 'c:\test.jpg', hide all.
  :::  
  ::: Example for /info:
  :::  
  ::: i_view32.exe c:\test.jpg /info=c:\test.txt
  ::: i_view32.exe c:\test.jpg /info=c:\jpgs.txt /fullinfo
  ::: i_view32.exe c:\*.jpg /info=c:\jpgs.txt
  :::  
  ::: Example for /append:
  :::  
  ::: i_view32.exe c:\test.jpg /append=c:\test.tif
  ::: Open 'c:\test.jpg ' and append it as page to 'c:\test.tif'.
  :::  
  ::: Example for /multitif:
  :::  
  ::: Syntax: /multitif=(tifname,file1,...,fileN)
  ::: First file is the name of the result TIF file.
  ::: i_view32.exe /multitif=(c:\test.tif,c:\test1.bmp,c:\dummy.jpg)
  ::: Create multipage TIF ('c:\test.tif') from 2 other images.
  :::  
  ::: Example for /panorama:
  :::  
  ::: Syntax: /panorama=(X,file1,...,fileN)
  ::: First parameter (X) is the direction: 1 = horizontal, 2 = vertical.
  ::: i_view32.exe /panorama=(1,c:\test1.bmp,c:\dummy.jpg)
  ::: Create horizontal panorama image from 2 other files.
  :::  
  ::: Example for /jpgq:
  :::  
  ::: i_view32.exe c:\test.jpg /jpgq=75 /convert=c:\new.jpg
  ::: Open 'c:\test.jpg' and save it as 'c:\new.jpg', quality = 75. Quality range: 1 - 100.
  :::  
  ::: Example for /tifc:
  :::  
  ::: i_view32.exe c:\test.jpg /tifc=4 /convert=c:\new.tif
  ::: Open 'c:\test.jpg' and save it as 'c:\new.tif', compression = Fax4.
  ::: Compressions: 0 = None, 1 = LZW, 2 = Packbits, 3 = Fax3, 4 = Fax4, 5 = Huffman, 6 = JPG, 7 = ZIP. 
  :::  
  ::: Example for /wall:
  :::  
  ::: i_view32.exe c:\test.jpg /wall=0
  ::: Open 'c:\test.jpg' and set is as wallpaper (centered).
  ::: wall values: 0 (centered), 1 (tiled), 2 (stretched), 3 (stretched-proportional)
  ::: i_view32.exe c:\images\*.jpg /random /wall=0 /killmesoftly
  ::: i_view32.exe /filelist=c:\mypics.txt /random /wall=0 /killmesoftly
  ::: Get random file from the folder/list and set as wallpaper.
  :::  
  ::: Example for /extract:
  :::  
  ::: i_view32.exe c:\multipage.tif /extract=(c:\temp,jpg)
  ::: Open 'c:\multipage.tif' and save all pages to folder 'c:\temp' as single JPGs.
  :::  
  ::: Example for EXE slideshow:
  :::  
  ::: MySlideshow.exe /monitor=2
  ::: => start standalone slideshow on monitor 2.
  ::: MySlideshow.exe /window=(0,0,800,600)
  ::: => start standalone slideshow in top left corner, window size 800x600.
  :::  
  ::: Example for /advancedbatch:
  :::  
  ::: i_view32.exe c:\test.jpg /advancedbatch /convert=c:\image.jpg
  ::: (some Misc. Advanced Batch options are not supported: overwrite, delete, subfolders, all pages)
  ::: Open c:\test.jpg', apply Advanced Batch options from the INI file and save as new file.
  :::  
  ::: Example for /jpg_rotate=(options):
  :::  
  ::: options = all 8 options from the JPG lossless dialog:
  ::: transformation, optimize, EXIF date, current date, set DPI, DPI value, marker option, custom markers
  ::: Note: this option will overwrite the original file(s)!
  ::: Values:
  ::: Transformation    : None (0), Vertical (1) ... Auto rotate (6) 
  ::: Optimize          : 0 or 1 
  ::: Set EXIF date    : 0 or 1 
  ::: Keep current date : 0 or 1 
  ::: Set DPI          : 0 or 1 
  ::: DPI value        : number 
  ::: Marker option    : Keep all (0), Clean all (1), Custom (2) 
  ::: Custom markers values (can be combined (add values)):
  :::  Keep Comment                1
  :::          Keep EXIF                  2
  :::          Keep IPTC                  4
  :::          Keep others                8
  ::: i_view32.exe c:\test.jpg /jpg_rotate=(6,1,1,0,1,300,0,0)
  ::: => Auto rotate, optimize, set EXIF date as file date, set DPI to 300, keep all markers
  ::: i_view32.exe c:\test.jpg /jpg_rotate=(6,1,1,0,0,0,2,6)
  ::: => Auto rotate, optimize, set EXIF date as file date, keep EXIF and IPTC markers
  ::: i_view32.exe c:\test.jpg /jpg_rotate=(3,1,0,1,0,0,1,0)
  ::: => Rotate 90, optimize, use current file date, clean all markers
  ::: i_view32.exe c:\images\*.jpg /jpg_rotate=(6,1,1,0,0,0,0,0)
  ::: => For all JPGs: Auto rotate, optimize, set EXIF date as file date, keep all markers
  :::  
  :::  
  :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   ::: 