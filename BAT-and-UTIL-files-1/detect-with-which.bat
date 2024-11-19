@Echo OFF
 on break cancel
:PUBLISH:
:DESCRIPTION:   detects the fully expanded filename of a command 
:DESCRIPTION:   if the command if it is an alias it just returns it back unexpanded (for reasons, we do not expand)
:DESCRIPTION:   if the command if it is an interna command, it just returns it back unexpanded (for reasons, we do not expand)
:DESCRIPTION:   
:USAGE:         validate-in-path {list of commands to validate}
:EXAMPLE:       validate-in-path foo foo.bat foo.exe alias
:COMPLICATIONS: When fully integrated, we end up in situations where %1 might be something like "dir/s" because windows lets us put / right after a command. That is addressed and can be tested with the listed tests.
:TESTING:       alias d=dir
:TESTING:       call detect-with-which d
:TESTING:       call detect-with-which d/s
:TESTING:       call detect-with-which dir
:TESTING:       call detect-with-which dir/s
:TESTING:       call detect-with-which ping
:TESTING:       call detect-with-which ping/s
:SIDE_EFECCTS:  None, but when we tried expanding aliases, dealing with aliases that had command separators would invariable send the part after the separator to our command line, which is very dangerous.
:REQUIRES:      print-message.bat (and other associated BAT files, but only for debug & error messaging)
:DEPENDENCIES:  validate-in-path.bat

REM Validate parameters
        set PARAM=%1
        set PARAMS=%*
        :all validate-in-path %param% sed.exe
        call validate-in-path         sed.exe
        set OUR_LOGGING_LEVEL=None

REM cleanse parameter: pull everything the / off of it in case it's something like "dir/s" or "d/s"
        set clean_param=%PARAM%
        if "%PARAM%" eq "" goto :NoParam
        if "%@REGEXSUB[1,(.*)/(.*),%PARAM]" ne "" (set clean_param=%@REGEXSUB[1,"(.*)/(.*)",%param])
        :NoParam
        call logging "param='%param%', clean_param is '%clean_param%'"


REM while it's possible to expand the alias, it's dangerous - 
REM if the alias contains command separator %+ then echoing it makes the part after %+ actually execute
REM so we will leave this as a do-nothing section in case this changes in the future
        if isAlias     %clean_param% (
            set RESULT=%clean_param% is an alias
            goto :IsAlias
        )
        if isInternal  %clean_param% (
            set RESULT=%clean_param% is an internal command
            goto :IsInternal
        )


REM execute the `which` command and  scrub our results:
        rem DEBUG: echo %ANSI_COLOR_DEBUG%%EMOJI_CALL_ME_HAND%  set tmp_which=%%@EXECSTR[which %clean_param]%ANSI_RESET%       
        set tmp_which=%@EXECSTR[which %clean_param]
        set RESULT=%tmp_which%
        if "%@REGEXSUB[2,(.*: )(.*),%tmp_which]" ne "" (set RESULT=%@REGEXSUB[2,"(.*: )(.*)",%tmp_which])


REM synonyms for results:
        :IsAlias
        :IsInternal
        call logging "result for $0 with parameters='%PARAM' is '%RESULT', tmp_which='%tmp_which'"
        set DETECTED=%RESULT%
        set    WHICH=%RESULT%
        set    FOUND=%RESULT%
        set     FILE=%RESULT%

