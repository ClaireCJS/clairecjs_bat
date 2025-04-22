@Echo OFF

rem Get parameters/give usage:
        if "" == "%1" .or. "" == "%2" (echo %ansi_color_warning_soft%USAGE: inline_progress_bar [step_num] [num_steps] %+ goto :END)
        set step_num=%1
        set num_steps=%2

rem If you want to simply copy this to a BAT file to use it faster, start after ‘rem ’ and change “:END” to “”:
        rem :inline_progress_bar [step_num num_steps]                                                                


rem Validate environment (once):
        iff "1" != "%validated_inline_progress_bar%" then
                call validate-environment-variables ansi_color_warning_soft ansi_cursor_invisible ansi_color_success ansi_cursor_visible
                call validate-is-function           randfg_soft ansi_move_to_col
                set  validated_inline_progress_bar=1       
        endiff


rem Store current position and total number of columns:
        set current_column=%_COLUMN
        set        columns=%_COLUMNS

rem Calculate the distance (aka length, width) of our message:
        set       distance=%@EVAL[%columns - %current_column% - 1]

rem Calculate how far along we are on that distance, rounding to the nearest despite a round function not existing:
        set       progress=%@EVAL[%@FLOOR[%@EVAL[((%step_num / %num_steps) * distance) + .5]]  ] 
        set      remaining=%@EVAL[%distance - %progress]

rem Draw our inline progress bar::
        echos %ansi_cursor_invisible%%ansi_color_success%%@repeat[=,%progress%]`>`%@randfg_soft[]%@repeat[%@char[9473],%remaining%]

rem Go back to where we started:
        echos %@ANSI_MOVE_TO_COL[%_COLUMN]%ansi_cursor_visible%

:END
