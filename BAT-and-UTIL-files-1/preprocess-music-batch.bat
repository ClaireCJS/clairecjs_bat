@Echo OFF

rem Remove any empty folders (file locking can leave these laying around)
        repeat 6 sweep rd *

rem Un-hide any hidden files
        attrib -rsh * /s

rem Collapse any cover-art folders into the current folder because that's how we like it
        sweep if isdir scans   (mv/ds scans   .)
        sweep if isdir cover   (mv/ds cover   .)
        sweep if isdir covers  (mv/ds covers  .)
        sweep if isdir artwork (mv/ds artwork .)

rem Convert any BMP files to JPG...
        sweep if exist *.bmp                   (echo asdf|call allbmp2jpg)

rem If cover art is "folder.jpg" and not "cover.jpg", rename it to "cover.jpg":
        sweep if exist folder.jpg .and. not exist cover.jpg (ren folder.jpg cover.jpg)

rem Certain files that we want automatically deleted:
        sweep if exist *.m3u                   (*del *.m3u)
        sweep if exist *.nfo                   (ren *.nfo README.txt)
        sweep if exist *.cue                   (ren *.cue cue.cue)
        sweep if exist *.ffp                   (ren *.ffp ffp.ffp)
        sweep if exist *.log                   (ren *.log log.log)
        sweep if exist  .DS_Store              (*del .DS_Store)
        sweep if exist  desktop.ini            (*del desktop.ini)
        sweep if exist "__ flac source __"     (*del "__ flac source __")
        sweep if exist "__ already renamed __" (*del "__ already renamed __")

