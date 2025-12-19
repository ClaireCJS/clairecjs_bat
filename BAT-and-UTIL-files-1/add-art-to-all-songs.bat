@Echo OFF
 on break cancel
 loadbtm ON



rem Validate environment once per session:
        iff "1" != "%validated_addarttoallsongs%" then
                if not defined filemask_audio call validate-environment-variable filemask_audio allwebp2jpg
                call validate-in-path randfg add-art-to-song warning print-message
                set validated_addarttoallsongs=1
        endiff


rem Convert cover art:
        iff exist cover.webp then
                iff not exist cover.jpg then
                        call allwebp2jpg
                        if exist cover.jpg .and. exist cover.webp *del cover.webp
                endiff
        endiff

rem Check for cover art:
        set cover=[NOT FOUND]
        if exist cover.webp set cover=cover.webp
        if exist cover.gif  set cover=cover.gif
        if exist cover.png  set cover=cover.png
        if exist cover.jpeg set cover=cover.jpeg
        if exist cover.jpg  set cover=cover.jpg


rem If no cover art found, intervene:
        :cover_art_check
        iff not exist %cover% then
                call warning "cover image could not be found"
                eset cover
                goto /i :cover_art_check
        endiff


rem Go through each song and add the art:       (changing color each time so we can tell where one begins and one ends)
        for %song in (%filemask_audio%) (
            call randfg
            echos .
            call add-art-to-song "%cover%" "%song%" 
        )


