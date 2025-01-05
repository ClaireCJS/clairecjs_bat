@Echo OFF

call validate-environment-variable FILEMASK_AUDIO%

for %%tmptmpfile in (%FILEMASK_AUDIO%) do echo false>"%@UNQUOTE["%tmptmpfile%"]:genius_searched_already"