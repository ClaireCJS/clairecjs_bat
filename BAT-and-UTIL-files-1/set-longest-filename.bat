@Echo OFF

:DESCRIPTION: call set-longest-filename - sets %LONGEST_FILENAME% variable to the longest filename in the folder and sets %LONGEST_FILENAME_LENGTH% equal to the length of that filename

set LONGEST_FILENAME_LENGTH=-1                                                                                                                
set NUM_FILES_HERE=0
for %%tmp_possible_longest_filename in (*.*) do (set NUM_FILES_HERE=%@EVAL[1 + %NUM_FILES_HERE%] %+ set len=%@LEN[%@UNQUOTE["%tmp_possible_longest_filename%"]] %+ if %len% gt %LONGEST_FILENAME_LENGTH% (set LONGEST_FILENAME_LENGTH=%len% %+ SET longest_filename=%tmp_possible_longest_filename%))



