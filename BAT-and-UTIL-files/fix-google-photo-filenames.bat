@Echo OFF

rem   This adds the hyphens back into the filenames & reformats filenames so we get "YYYY-MM-DD HHMM - " formatted filenames

rem   Example renamings:
            rem :⭢︋📂20230107_232125546.MP.jpg -> 2023-01-07 2321 - 32125546.MP.jpg
            rem :⭢︋📂20230107_232126848.jpg    -> 2023-01-07 2321 - 32126848.jpg
            rem :⭢︋📂20230107_232128116.jpg    -> 2023-01-07 2321 - 32128116.jpg
            rem :⭢︋📂20230107_232129440.MP.jpg -> 2023-01-07 2321 - 32129440.MP.jpg



rem First remove "PXL_" at the beginnings of filenames:

    for %myfile in (PXL_*.jpg;PXL_*.mp4) ren "%myfile" "%@SUBSTR[%myfile,4,9999]"



rem then do the actual formatting:

    for %1 in (20[0-9][0-9][01][0-9][0-3][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]*.jpg;20[0-9][0-9][01][0-9][0-3][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]*.mp4)  mv "%1" "%@SUBSTR[%1,0,4]-%@SUBSTR[%1,4,2]-%@SUBSTR[%1,6,2] %@SUBSTR[%1,9,4] - %@SUBSTR[%1,10]"

