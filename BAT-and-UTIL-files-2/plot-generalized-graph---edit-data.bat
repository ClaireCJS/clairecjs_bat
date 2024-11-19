@Echo OFF
@on break cancel

::::: INITIAL DEPLOYMENT SETUP ONLY:
    set WHAT_WE_ARE_TRACKING=something

::::: SETUP:
    call plot-%WHAT_WE_ARE_TRACKING%-graph---plot-graph DEFINE_CONSTANTS_ONLY
    if exist "%TRACKING_FILE%" (goto :Exists)
            %COLOR_WARNING%   %+ echo ** Tracking file does not exist! Ctrl-Break to prevent creation... %+ %COLOR_NORMAL%
            pause  %+  pause  %+ pause  %+  pause  
            %COLOR_IMPORTANT% %+ echo ** Creating tracking file %TRACKING_FILE% ...                      %+ %COLOR_NORMAL%
            >"%TRACKING_FILE%"
    :Exists
    call validate-environment-variables TRACKING_FILE WHAT_WE_ARE_TRACKING
    call checkeditor

::::: EDIT VALUES:
    %EDITOR% "%TRACKING_FILE%"
