@Echo off
 on break cancel


rem 🔍Validate environment:
        call checkeditor
        call validate-in-path findstr sleep success
        call validate-environment-variables italics_on italics_off faint_on faint_off 
        set  validated_eset=1

rem ✏Get value to search for (or rather, to search for the absence of):
         set The_String_That_We_Do_NOT_Want_Included_In_The_Files_We_Wish_To_Edit=on break
        eset The_String_That_We_Do_NOT_Want_Included_In_The_Files_We_Wish_To_Edit /p
        
rem ✏Get files to search:
         set the_Files_We_Want_To_Search_Through=c*.bat
        eset the_Files_We_Want_To_Search_Through /p
        
rem 🔎Validate that the files to search even exist:
        call validate-environment-variable the_Files_We_Want_To_Search_Through

rem ➰Loop through all the files in the current directory and edit them if they meet the criteria:
        for %%tmpFile in (%the_Files_We_Want_To_Search_Through%) do (
                on break cancel
                rem Check if the file contains our string:   
                set EDIT=0
                echo findstr /i /c:"%The_String_That_We_Do_NOT_Want_Included_In_The_Files_We_Wish_To_Edit%" "%TmpFile" 
                findstr /i /c:"%The_String_That_We_Do_NOT_Want_Included_In_The_Files_We_Wish_To_Edit%" "%tmpFile" >nul 2>&1
                if errorlevel 1 set EDIT=1
                iff 1 eq %EDIT then                
                        rem echo Editing %faint_on%%tmpFile%%faint_off%%newline%%tab%...because it does %italics_on%not%italics_off% contain '%italics_on%%The_String_That_We_Do_NOT_Want_Included_In_The_Files_We_Wish_To_Edit%%italics_off%'
                         %EDITOR% "c:\bat\%tmpFile"
                         *delay 2 /b /f
                endiff
        )

rem 🎉Let us know of success:
        call success "All applicable %italics_on%%the_Files_We_Want_To_Search_Through%%italics_off% files have been edited."
