@Echo OFF

call warning "%0 - so it turns out our @FINDFIRST has a bug, so the file we are opening %italics_on%may%italics_off% not actually be the first."
rem TODO possibly report bug to TCC forum, though this may have already happened, and it may already be fixed

call validate-environment-variable FILEMASK_IMAGE
call run-first-file-in-directory  %FILEMASK_IMAGE%
