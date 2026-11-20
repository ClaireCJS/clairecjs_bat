@echo %ansi_reset%%conceal_off%%ansi_color_grey%📞📞📞 “%0 %1$” called by %_PBATCHNAME 📞📞📞%ansi_color_normal% %+ *if defined BATCHLINE .and. "%BATCHLINE%" != "-1" *echoerr 🚩 %ANSI_COLOR_ERROR%     Line number:  %italics%%unknown_command_highlight_color%%BATCHLINE%%ANSI_COLOR_ERROR%%italics_off% %ansi_color_normal%

@on break cancel
@echo off

set IRFANVIEW=%UTIL2%\IRFANVIEWPORTABLE\App\IrfanView64\i_view64.exe
if not exist "%IRFANVIEW%" call validate-environment-variable IRFANVIEW



 echo start "" "%IRFANVIEW%" %*
      start "" "%IRFANVIEW%" %*
 
rem  :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   ::: 
rem  :::  
rem  ::: See the file "i_options.txt" (IrfanView folder) for the most recent version on all command line options.
rem  :::  
rem  ::: Command line options allow you to set some functions of IrfanView before the viewer is launched.
rem  :::  
rem  ::: These command line options are supported in IrfanView:
rem  :::  
rem  ::: /one -        force 'Only one instance' 
rem  ::: /fs -        force Full Screen display 
rem  ::: /bf -        force 'Fit images to desktop' display option 
rem  ::: /title=text -        set window title to 'text' 
rem  ::: /pos=(x,y) -        move the window to x,y 
rem  ::: /convert=filename -        convert input file to 'filename' and CLOSE IrfanView  
rem  :::           (see Pattern page for additional filename options)
rem  ::: /slideshow=txtfile -        play slideshow with the files from 'txtfile' 
rem  ::: /slideshow=folder -        play slideshow with the files from 'folder' 
rem  ::: /reloadonloop -        reload input source used in /slideshow when list finished 
rem  ::: /filelist=txtfile -        use filenames from "txtfile" as input, see examples below 
rem  ::: /thumbs -        force thumbnails 
rem  ::: /killmesoftly -        close all IrfanView instances (exit after command line) 
rem  ::: /cmdexit -        close current IrfanView after command line processing 
rem  ::: /closeslideshow -        close slideshow and close IrfanView after the last image 
rem  ::: /page=X -        open page number X from a multipage input image 
rem  ::: /crop=(x,y,w,h) -        crop input image: x-start, y-start, width, height 
rem  ::: /print -        print input image to default printer and close IrfanView 
rem  ::: /print="Name" -        print input image to specific printer and close IrfanView 
rem  ::: /resize=(w,h) -        resize input image to w (width) and h (height) 
rem  ::: /resize_long=X -        resize input image: set long side to X 
rem  ::: /resize_short=X -        resize input image: set short side to X 
rem  ::: /resample -        for resize: use Resample option (better quality) 
rem  ::: /capture=X -        capture the screen or window (see examples below) 
rem  ::: /ini -        use the Windows folder for INI/LST files (read/save) 
rem  ::: /ini="Folder" -        use the folder "Folder" for INI/LST files (read/save) 
rem  ::: /clippaste -        paste image from the clipboard 
rem  ::: /clipcopy -        copy image to the clipboard 
rem  ::: /silent -        don't show error messages for command line read/save errors 
rem  ::: /invert -        invert the input image (negative) 
rem  ::: /dpi=(x,y) -        change DPI values, set DPIs for scanning 
rem  ::: /scan -        acquire the image from the TWAIN device - show TWAIN dialog 
rem  ::: /scanhidden -        acquire the image from the TWAIN device - hide TWAIN dialog 
rem  ::: /batchscan=(options) -        simulate menu: File->Batch Scanning, see examples below 
rem  ::: /bpp=BitsPerPixel -        change color depth of the input image to BitsPerPixel 
rem  ::: /swap_bw -        swap black and white color 
rem  ::: /gray -        convert input image to grayscale 
rem  ::: /rotate_r -        rotate input image to right 
rem  ::: /rotate_l -        rotate input image to left 
rem  ::: /hflip -        horizontal flip 
rem  ::: /vflip -        vertical flip 
rem  ::: /filepattern="x" -        browse only specific files 
rem  ::: /sharpen=X -        open image and apply the sharpen filter value X 
rem  ::: /effect=(X,p1,p2) -        apply effect filter X, see below for examples 
rem  ::: /contrast=X -        open image and apply the contrast value X 
rem  ::: /bright=X -        open image and apply the brighntess value X 
rem  ::: /gamma=X -        open image and apply the gamma correction value X 
rem  ::: /advancedbatch -        apply Advanced Batch Dialog options to image (from INI file) 
rem  ::: /hide=X -        hide toolbar, status bar, menu and/or caption of the main window (see examples below) 
rem  ::: /transpcolor=(r,g,b) -        set transparent color if saving as GIF/PNG/ICO 
rem  ::: /aspectratio -        used for /resize and /resample, keep image proportions 
rem  ::: /info=txtfile -        write image infos to "txtfile" 
rem  ::: /fullinfo -        used for /info, write EXIF, IPTC and Comment data 
rem  ::: /append=tiffile -        append image as (TIF) page to "tiffile" 
rem  ::: /multitif=(tif,files) -        create multipage TIF from input files 
rem  ::: /panorama=(X,files) -        create panorama image from input files; X = direction (1 or 2) 
rem  ::: /jpgq=X -        set JPG save quality 
rem  ::: /tifc=X -        set TIF save compression 
rem  ::: /wall=X -        set image as wallpaper; see below for /random and examples 
rem  ::: /extract=(folder,ext) -        extract all pages from a multipage file 
rem  ::: /import_pal=palfile -        import and apply a special palette to the image (PAL format) 
rem  ::: /export_pal=palfile -        export image palette to file (PAL format) 
rem  ::: /jpg_rotate=(options) -        JPG lossless rotation, see examples below 
rem  ::: /monitor=X -        start EXE-Slideshow on monitor X  
rem  ::: /window=(x,y,w,h) -        set EXE-Slideshow window position and size 
rem  :::  
rem  :::  
rem  ::: Notes:
rem  :::  
rem  ::: - Only lower case options are supported (don't type any UPPERCASE letters) !
rem  ::: - Input file name (if required) is always the first parameter!
rem  ::: - Use "" for file names with spaces, example: "c:\images\dummy test file.jpg".
rem  ::: - Write always the FULL paths for file names (incl. drive letter).
rem  ::: - You can combine several options in one command.
rem  ::: - Wildcards (*) supported only for /convert, /print, /info and /jpg_rotate.
rem  ::: - Maximal command line length is limited by Windows, so use shorter names/paths.
rem  ::: - Most settings are loaded from the INI file. Using prepared INIs and /ini=folder option, you can extend the possibilities.
rem  ::: - IrfanView exit code is 0. If /convert or /print is used, there is 1 or 2 also possible, for load/save errors.
rem  :::  
rem  :::  
rem  ::: Example for conversion:
rem  :::  
rem  ::: i_view32.exe c:\test.bmp /convert=c:\test.jpg
rem  ::: Convert file: 'c:\test.bmp' to 'c:\test.jpg' without GUI.
rem  :::  
rem  ::: i_view32.exe c:\*.jpg /convert=d:\temp\*.gif
rem  ::: i_view32.exe c:\*.jpg /resize=(500,300) /convert=d:\temp\*.png
rem  ::: i_view32.exe c:\*.jpg /resize=(500,300) /aspectratio /resample /convert=d:\temp\*.png
rem  ::: i_view32.exe /filelist=c:\mypics.txt /resize=(500,300) /aspectratio /resample /convert=d:\temp\*.png
rem  ::: i_view32.exe c:\test.bmp /convert=c:\test_$Wx$H.jpg
rem  ::: i_view32.exe c:\test.bmp /resize=(100,100) /resample /aspectratio /convert=d:\$N_thumb.jpg
rem  ::: i_view32.exe c:\test.bmp aspectratio /convert=d:\temp\$T(%Y%m%d)\test_$Wx$H.jpg
rem  ::: i_view32.exe c:\test.bmp /convert=$D$N.jpg
rem  ::: i_view32.exe c:\*.bmp /convert=$D$N.jpg
rem  ::: i_view32.exe c:\*.jpg /advancedbatch /convert=c:\temp\*.jpg
rem  ::: i_view32.exe c:\test.bmp /transpcolor=(255,255,255) /convert=c:\giftest.gif
rem  ::: (Note: Supported are all IrfanView read/save formats except audio/video.) 
rem  :::  
rem  ::: Example for slideshow:
rem  :::  
rem  ::: i_view32.exe /slideshow=c:\mypics.txt
rem  ::: (Note: The file 'c:\mypics.txt' contains, in each line, a name of an image, including the full path OR path relative to "i_view32.exe".) 
rem  :::  
rem  ::: i_view32.exe /slideshow=c:\mypics.txt /reloadonloop
rem  ::: i_view32.exe /slideshow=c:\images\
rem  ::: i_view32.exe /slideshow=c:\images\ /reloadonloop
rem  ::: i_view32.exe /slideshow=c:\images\*.jpg
rem  ::: i_view32.exe /slideshow=c:\images\test*.jpg
rem  ::: You have to close IrfanView after the last image from the TXT file, if not /closeslideshow is used.
rem  :::  
rem  ::: Example for /closeslideshow:
rem  :::  
rem  ::: i_view32.exe /slideshow=c:\mypics.txt /closeslideshow
rem  ::: IrfanView will be closed after the last image from 'c:\mypics.txt'.
rem  :::  
rem  ::: Example for thumbnails:
rem  :::  
rem  ::: i_view32.exe c:\test\image1.jpg /thumbs
rem  ::: Open 'image1.jpg' and display thumbnails from directory 'c:\test'.
rem  :::  
rem  ::: i_view32.exe c:\test\ /thumbs
rem  ::: Display thumbnails from directory 'c:\test'.
rem  :::  
rem  ::: i_view32.exe /filelist=c:\mypics.txt /thumbs
rem  ::: Load filenames from TXT file and display as thumbnails.
rem  :::  
rem  ::: Example for filelist:
rem  :::  
rem  ::: i_view32.exe /filelist=c:\mypics.txt
rem  ::: i_view32.exe /filelist=c:\mypics.txt /convert=d:\test\*.jpg
rem  ::: i_view32.exe /filelist=c:\mypics.txt /thumbs
rem  :::  
rem  ::: Example for close:
rem  :::  
rem  ::: i_view32.exe /killmesoftly
rem  ::: Close IrfanView and terminate all instances.
rem  :::  
rem  ::: Example for /page:
rem  :::  
rem  ::: i_view32.exe c:\test.tif /page=3
rem  ::: Open page number 3 from the multipage image 'c:\test.tif'.
rem  :::  
rem  ::: Example for /crop:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /crop=(10,10,300,300)
rem  ::: i_view32.exe c:\test.jpg /crop=(10,10,300,300) /convert=c:\giftest.gif
rem  ::: Open 'c:\test.jpg' and crop: x-start=10, y-start=10, width=300, height=300 (in pixels).
rem  :::  
rem  ::: Example for /print:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /print
rem  ::: Open 'c:\test.jpg', print the image to default printer and close IrfanView.
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /print="Printer Name"
rem  ::: Open 'c:\test.jpg', print the image to specific printer and close IrfanView.
rem  :::  
rem  ::: i_view32.exe c:\*.jpg /print
rem  ::: Print all JPGs from "C:\" and close IrfanView.
rem  :::  
rem  ::: Note: The actual settings from the INI file are used.
rem  :::  
rem  ::: Example for /resize:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /resize=(300,300) /resample
rem  ::: Open 'c:\test.jpg' and resample: width=300, height=300.
rem  ::: (Note: Resample uses the active resample filter from the INI file.)
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /resize=(300,300) /aspectratio
rem  ::: Open 'c:\test.jpg' and resize: width= max. 300, height= max. 300, proportional.
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /resize_long=300 /aspectratio /resample
rem  ::: Open 'c:\test.jpg' and resample: long side=300, short side=proportional.
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /resize=(300,0)
rem  ::: Open 'c:\test.jpg' and resize: width=300, height=original.
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /resize=(300,0) /aspectratio
rem  ::: Open 'c:\test.jpg' and resize: width=300, height=proportional.
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /resize=(150p,150p)
rem  ::: Open 'c:\test.jpg' and resize: width=150%, height=150%.
rem  :::  
rem  ::: Example for /capture:
rem  :::  
rem  ::: i_view32.exe /capture=0
rem  ::: Capture the whole screen.
rem  ::: i_view32.exe /capture=6
rem  ::: Start in Capture mode, use last used capture dialog settings.
rem  :::  
rem  ::: capture values: 
rem  ::: 0 = whole screen 
rem  ::: 1 = current monitor, where mouse is located
rem  ::: 2 = foreground window
rem  ::: 3 = foreground window - client area
rem  ::: 4 = rectangle selection
rem  ::: 5 = object selected with the mouse
rem  ::: 6 = start in capture mode (can't be combined with other commandline options)
rem  :::  
rem  ::: Advanced examples:
rem  ::: i_view32.exe /capture=2 /convert=c:\test.jpg
rem  ::: Capture foreground window and save result as file.
rem  ::: i_view32.exe /capture=2 /convert=c:\capture_$U(%d%m%Y_%H%M%S).jpg
rem  ::: Capture foreground window and save result as file; the file name contains time stamp.
rem  :::  
rem  ::: Example for /ini:
rem  :::  
rem  ::: i_view32.exe /ini
rem  ::: i_view32.exe c:\test.jpg /ini
rem  ::: i_view32.exe c:\test.jpg /ini="c:\temp\"
rem  :::  
rem  ::: Example for /clippaste:
rem  :::  
rem  ::: i_view32.exe /clippaste
rem  ::: i_view32.exe /clippaste /convert=c:\test.gif
rem  :::  
rem  ::: Example for /clipcopy:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /clipcopy
rem  ::: i_view32.exe c:\test.jpg /clipcopy /killmesoftly
rem  :::  
rem  ::: Example for /invert:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /invert
rem  :::  
rem  ::: Example for /dpi:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /dpi=(72,72)
rem  :::  
rem  ::: Example for /scan:
rem  :::  
rem  ::: With the scan command, you can only combine: /print, /dpi, /gray and /convert. 
rem  ::: i_view32.exe /scan
rem  ::: i_view32.exe /scanhidden
rem  ::: i_view32.exe /scanhidden /dpi=(150,150)
rem  ::: i_view32.exe /scan /convert=c:\test.gif
rem  ::: i_view32.exe /scanhidden /gray /convert=c:\test.gif
rem  ::: i_view32.exe /print /scan
rem  :::  
rem  ::: Example for /batchscan=(options):
rem  :::  
rem  ::: options = all 8 options from the batch scanning dialog:
rem  ::: filename, index, increment, digits, skip, dest-folder, save-extension, multi-tif
rem  ::: i_view32.exe /batchscan=(scanfile,1,1,2,1,c:\temp,bmp,0)
rem  ::: i_view32.exe /batchscan=(scanfile,1,1,2,1,c:\temp,bmp,0) /dpi=(150,150)
rem  ::: i_view32.exe /batchscan=(scanfile,1,1,2,0,c:\temp,tif,1)
rem  ::: i_view32.exe /batchscan=("crazy, filename",1,1,2,0,"c:\temp\crazy, (folder)",tif,1)
rem  ::: i_view32.exe /batchscan=(scanfile,1,1,2,1,c:\temp,bmp,0) /scanhidden
rem  :::  
rem  ::: Example for /bpp:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /bpp=8
rem  ::: Open 'c:\test.jpg' and reduce to 256 colors. Supported BPP-values: 1, 4, 8 and 24 (decrease/increase color depth).
rem  :::  
rem  ::: Example for /filepattern:
rem  :::  
rem  ::: i_view32.exe c:\images\  /filepattern="*.jpg"
rem  ::: Go to folder "'c:\images" and load JPGs only in the browse/file list.
rem  :::  
rem  ::: i_view32.exe c:\images\ /thumbs /filepattern="*.jpg"
rem  ::: Go to folder "'c:\images" and show JPG thumbnails only.
rem  :::  
rem  ::: i_view32.exe c:\images\ /thumbs /filepattern="123*.jpg"
rem  ::: Go to folder "'c:\images" and show JPG with names "123*" as thumbnails.
rem  :::  
rem  ::: Example for /effect=(effect-nr,param1,param2)::
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /effect=(6,3,0) 
rem  ::: Apply Median filter, parameter = 3.
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /effect=(2,3,50) 
rem  ::: Apply Blur-2 filter, parameter1 = 3, parameter2 = 50.
rem  :::  
rem  ::: effect-nr values: (from Effect-Browser dialog): 
rem  ::: 1 = Blur
rem  ::: 2 = Blur-2
rem  ::: ...
rem  ::: 37 = Metallic Ice
rem  :::  
rem  ::: Example for /sharpen:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /sharpen=33
rem  :::  
rem  ::: Example for /hide:
rem  :::  
rem  ::: Values (can be combined (add values)):
rem  ::: Toolbar 1 
rem  ::: Status bar 2 
rem  ::: Menu bar 4 
rem  ::: Caption 8 
rem  ::: i_view32.exe c:\test.jpg /hide=1
rem  ::: Open 'c:\test.jpg', hide toolbar only.
rem  ::: i_view32.exe c:\test.jpg /hide=3
rem  ::: Open 'c:\test.jpg', hide toolbar and status bar.
rem  ::: i_view32.exe c:\test.jpg /hide=12
rem  ::: Open 'c:\test.jpg', hide caption and menu bar.
rem  ::: i_view32.exe c:\test.jpg /hide=15
rem  ::: Open 'c:\test.jpg', hide all.
rem  :::  
rem  ::: Example for /info:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /info=c:\test.txt
rem  ::: i_view32.exe c:\test.jpg /info=c:\jpgs.txt /fullinfo
rem  ::: i_view32.exe c:\*.jpg /info=c:\jpgs.txt
rem  :::  
rem  ::: Example for /append:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /append=c:\test.tif
rem  ::: Open 'c:\test.jpg ' and append it as page to 'c:\test.tif'.
rem  :::  
rem  ::: Example for /multitif:
rem  :::  
rem  ::: Syntax: /multitif=(tifname,file1,...,fileN)
rem  ::: First file is the name of the result TIF file.
rem  ::: i_view32.exe /multitif=(c:\test.tif,c:\test1.bmp,c:\dummy.jpg)
rem  ::: Create multipage TIF ('c:\test.tif') from 2 other images.
rem  :::  
rem  ::: Example for /panorama:
rem  :::  
rem  ::: Syntax: /panorama=(X,file1,...,fileN)
rem  ::: First parameter (X) is the direction: 1 = horizontal, 2 = vertical.
rem  ::: i_view32.exe /panorama=(1,c:\test1.bmp,c:\dummy.jpg)
rem  ::: Create horizontal panorama image from 2 other files.
rem  :::  
rem  ::: Example for /jpgq:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /jpgq=75 /convert=c:\new.jpg
rem  ::: Open 'c:\test.jpg' and save it as 'c:\new.jpg', quality = 75. Quality range: 1 - 100.
rem  :::  
rem  ::: Example for /tifc:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /tifc=4 /convert=c:\new.tif
rem  ::: Open 'c:\test.jpg' and save it as 'c:\new.tif', compression = Fax4.
rem  ::: Compressions: 0 = None, 1 = LZW, 2 = Packbits, 3 = Fax3, 4 = Fax4, 5 = Huffman, 6 = JPG, 7 = ZIP. 
rem  :::  
rem  ::: Example for /wall:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /wall=0
rem  ::: Open 'c:\test.jpg' and set is as wallpaper (centered).
rem  ::: wall values: 0 (centered), 1 (tiled), 2 (stretched), 3 (stretched-proportional)
rem  ::: i_view32.exe c:\images\*.jpg /random /wall=0 /killmesoftly
rem  ::: i_view32.exe /filelist=c:\mypics.txt /random /wall=0 /killmesoftly
rem  ::: Get random file from the folder/list and set as wallpaper.
rem  :::  
rem  ::: Example for /extract:
rem  :::  
rem  ::: i_view32.exe c:\multipage.tif /extract=(c:\temp,jpg)
rem  ::: Open 'c:\multipage.tif' and save all pages to folder 'c:\temp' as single JPGs.
rem  :::  
rem  ::: Example for EXE slideshow:
rem  :::  
rem  ::: MySlideshow.exe /monitor=2
rem  ::: => start standalone slideshow on monitor 2.
rem  ::: MySlideshow.exe /window=(0,0,800,600)
rem  ::: => start standalone slideshow in top left corner, window size 800x600.
rem  :::  
rem  ::: Example for /advancedbatch:
rem  :::  
rem  ::: i_view32.exe c:\test.jpg /advancedbatch /convert=c:\image.jpg
rem  ::: (some Misc. Advanced Batch options are not supported: overwrite, delete, subfolders, all pages)
rem  ::: Open c:\test.jpg', apply Advanced Batch options from the INI file and save as new file.
rem  :::  
rem  ::: Example for /jpg_rotate=(options):
rem  :::  
rem  ::: options = all 8 options from the JPG lossless dialog:
rem  ::: transformation, optimize, EXIF date, current date, set DPI, DPI value, marker option, custom markers
rem  ::: Note: this option will overwrite the original file(s)!
rem  ::: Values:
rem  ::: Transformation    : None (0), Vertical (1) ... Auto rotate (6) 
rem  ::: Optimize          : 0 or 1 
rem  ::: Set EXIF date    : 0 or 1 
rem  ::: Keep current date : 0 or 1 
rem  ::: Set DPI          : 0 or 1 
rem  ::: DPI value        : number 
rem  ::: Marker option    : Keep all (0), Clean all (1), Custom (2) 
rem  ::: Custom markers values (can be combined (add values)):
rem  :::  Keep Comment                1
rem  :::          Keep EXIF                  2
rem  :::          Keep IPTC                  4
rem  :::          Keep others                8
rem  ::: i_view32.exe c:\test.jpg /jpg_rotate=(6,1,1,0,1,300,0,0)
rem  ::: => Auto rotate, optimize, set EXIF date as file date, set DPI to 300, keep all markers
rem  ::: i_view32.exe c:\test.jpg /jpg_rotate=(6,1,1,0,0,0,2,6)
rem  ::: => Auto rotate, optimize, set EXIF date as file date, keep EXIF and IPTC markers
rem  ::: i_view32.exe c:\test.jpg /jpg_rotate=(3,1,0,1,0,0,1,0)
rem  ::: => Rotate 90, optimize, use current file date, clean all markers
rem  ::: i_view32.exe c:\images\*.jpg /jpg_rotate=(6,1,1,0,0,0,0,0)
rem  ::: => For all JPGs: Auto rotate, optimize, set EXIF date as file date, keep all markers
rem  :::  
rem  :::  
rem  :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   :::   ::: 