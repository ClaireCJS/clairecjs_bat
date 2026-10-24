@Echo OFF


set DOCS=%BAT%\docs
if not isdir %BAT%  call validate-environment-variable BAT
if not isdir %DOCS% call validate-environment-variable DOCS


set TEMP_DOC_C4S=%BAT%\clips4sale_downloader\README.md
set TEMP_DOC_AMB=%BAT%\audit_music_batch\README.md
set TEMP_DOC_IGF=%BAT%\image_caption_gender_fixer\README.md
set TEMP_DOC_PAF=%BAT%\PAFPlayer\PAFPlayer.md

call validate-environment-variables TEMP_DOC_C4S TEMP_DOC_AMB TEMP_DOC_IGF TEMP_DOC_PAF

                                     
echos %@randcolor_soft[] %+ *copy /u /Ns %BAT%\*.md     %DOCS%
echos %@randcolor_soft[] %+ *copy /u /Ns %TEMP_DOC_C4S% %DOCS%\clips4sale-preview-downloader.md
echos %@randcolor_soft[] %+ *copy /u /Ns %TEMP_DOC_AMB% %DOCS%\audit-music-batch.md
echos %@randcolor_soft[] %+ *copy /u /Ns %TEMP_DOC_IGF% %DOCS%\image-caption-gender-fixer.md
echos %@randcolor_soft[] %+ *copy /u /Ns %TEMP_DOC_PAF% %DOCS%\PAFPlayer.md

