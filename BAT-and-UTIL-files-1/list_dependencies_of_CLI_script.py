#pylint: disable=C0301,C0114,C0103,R0912,R0915,R1702,W1203


#TASK - does it detect commands in if statements , with and without parens
        #subtask: for/do as well

#TASK - grab all files from all paths in advance so all our path searches are done internally

#GOAL: get through all validation successfully


import os
import re
import sys
import shlex
import logging
import argparse
#import itertools
from colorama import Fore, Back, Style, init
import clairecjs_utils as claire
init(autoreset=False)


COMMAND_SEPARATORS     = ["^", "%+"]
VALIDATABLE_EXTENSIONS = ['.BAT', '.BTM', '.CMD']       #we throw an error and refuse to process unless we're passed one of these extensions
EXECUTABLE_EXTENSIONS  = [".BAT", ".BTM", ".PY", ".PL", ".EXE", ".CMD", ".PM", ".MSI", ".JAR", ".RB", ".SH", ".PHP", ".JS", ".VBS", ".WSF", ".PS1", ".PSM1", ".CPL", ".SCR", ".COM", ".GADGET", ".INF1", ".PAF", ".U3P", ".JNLP", ".APPLICATION", ".WS", ".VBE", ".VBSCRIPT", ".WORKFLOW", ".APPREF-MS", ".MSC", ".MSP", ".HTA", ".REG", ".DLL", ".OCX", ".SYS", ".CPL", ".DRV", ".INS", ".INX", ".ISU", ".JOB", ".OUT", ".PAF", ".PIF", ".RUN", ".RGS", ".SCT", ".SHB", ".SHS", ".U3P", ".VB", ".VBE", ".VBS", ".VBSCRIPT", ".WORKFLOW"]
INTERNAL_COMMANDS      = ["ACTIVATE", "ALIAS", "ASSOC", "ASSOCIATE", "ATTRIB", "BATCOMP", "BDEBUGGER", "BEEP", "BREAK", "BREAKPOINT", "BTMONITOR", "BZIP2", "CALL", "CANCEL", "CAPTURE", "CD", "CDD", "CHCP", "CHDIR", "CHRONIC", "CLIP", "CLIPMONITOR", "CLS", "COLOR", "COMMANDS", "COMMENT", "COPY", "COPYDIR", "DATE", "DATEMONITOR", "DEBUGMONITOR", "DEBUGSTRING", "DEDUPE", "DEFER", "DEL", "DELAY", "DESCRIBE", "DESKTOP", "DETACH", "DIFFER", "DIR", "DIRHISTORY", "DIRS", "DISKMONITOR", "DNS", "DO", "DRAWBOX", "DRAWHLINE", "DRAWVLINE", "ECHO", "ECHO.", "ECHOERR", "ECHOERR.", "ECHOS", "ECHOS.", "ECHOSERR", "ECHOSERR.", "ECHOX", "ECHOX.", "ECHOXERR", "ECHOXERR.", "EJECTMEDIA", "ENDLOCAL", "ENUMPROCESSES", "ENUMSERVERS", "ENUMSHARES", "ERASE", "ESET", "EVENTLOG", "EVENTMONITOR", "EVERYTHING", "EXCEPT", "EXIT", "FFIND", "FILELOCK", "FIREWIREMONITOR", "FOLDERMONITOR", "FONT", "FOR", "FREE", "FTYPE", "FUNCTION", "GLOBAL", "GOSUB", "GOTO", "GZIP", "HASH", "HEAD", "HELP", "HISTORY", "IF", "IFF", "IFTP", "INKEY", "INPUT", "INSTALLED", "JABBER", "JAR", "JUMPLIST", "KEYBD", "KEYS", "KEYSTACK", "LIBRARY", "LIST", "LOADBTM", "LOADMEDIA", "LOCAL", "LOCKMONITOR", "LOG", "LUA", "MD", "MEMORY", "MKDIR", "MKLINK", "MKLNK", "MONITOR", "MOUNTISO", "MOUNTVHD", "MOVE", "MOVEDIR", "MSGBOX", "NETMONITOR", "NOTIFY", "ODBC", "ON", "OPTION", "OSD", "PATH", "PAUSE", "PDIR", "PEE", "PLAYAVI", "PLAYSOUND", "PLUGIN", "POPD", "POSTMSG", "POWERMONITOR", "PRINT", "PRINTF", "PRIORITY", "PROCESSMONITOR", "PROMPT", "PSHELL", "PSUBST", "PUSHD", "QUERYBOX", "QUIT", "RD", "REBOOT", "RECORDER", "RECYCLE", "REGMONITOR", "REPEAT", "RESOLUTION", "RESTOREPOINT", "REXEC", "REM", "REN", "RENAME", "RETURN", "RMDIR", "RSHELL", "SAVECONSOLE", "SCREEN", "SCREENMONITOR", "SCRPUT", "SELECT", "SENDHTML", "SENDMAIL", "SERVICEMONITOR", "SERVICES", "SET", "SETARRAY", "SETDOS", "SETLOCAL", "SETP", "SHIFT", "SHORTCUT", "SHRALIAS", "SMPP", "SNMP", "SNPP", "SPONGE", "SSHEXEC", "START", "STATUSBAR", "SWITCH", "SYNC", "TABCOMPLETE", "TAIL", "TAR", "TASKBAR", "TASKDIALOG", "TASKEND", "TASKLIST", "TCDIALOG", "TCFILTER", "TCFONT", "TCTOOLBAR", "TEE", "TEXT", "THREAD", "TIME", "TIMER", "TITLE", "TOAST", "TOUCH", "TPIPE", "TRANSIENT", "TREE", "TRUENAME", "TS", "TYPE", "UNALIAS", "UNBZIP2", "UNFUNCTION", "UNGZIP", "UNJAR", "UNLIBRARY", "UNTAR", "UNMOUNTISO", "UNMOUNTVHD", "UNQLITE", "UNSET", "UNSETARRAY", "UNSETP", "UNZIP", "USBMONITOR", "Monitor USB devices", "VBEEP", "Flash the screen and beep", "VDESKTOP", "VER", "VERIFY", "VIEW", "VOL", "VSCRPUT", "WAKEONLAN", "WEBFORM", "WEBUPLOAD", "WHICH", "WINDOW", "WMIQUERY", "WMIRUN", "Y", "ZIP", "ZIPSFX", "7UNZIP", "7ZIP",                            "\x1A",                                   "ELSEIFF", "ELSE", "ENDIFF", "ENDTEXT", "ITERATE", "LEAVE", "ENDDO", "CASE", "DEFAULT", "ENDSWITCH", "ENDCOMMENT","NOT",".AND.",".OR.","EXIST","IN"]               #copied from documentation but all echo commands have a 2nd entry with "." after them because of the weird "echo." exception. Also, at the end, we add '\x1A', which is an EOF character that somehow got encoded into a bunch of BAT files in the 1990s, and while not valid, doesn't hurt things, and are around more  than we care to fix. Just ignore them. After that, starting with ELSEIFF, are technically not commands, but keywords used with commands. We could break these out into separate lists for formality if we were so inclined.
ECHO_COMMANDS          = ["ECHO", "ECHO.", "ECHOERR", "ECHOERR.", "ECHOS", "ECHOS.", "ECHOSERR", "ECHOSERR.", "ECHOX", "ECHOX.", "ECHOXERR", "ECHOXERR."]
SKIP_ARGUMENT_PROCESSING_OF_THESE_COMMANDS = ECHO_COMMANDS + ["REM", "COLOR"]
CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER = ["START","WRAPPER","SPL","SPLH","SPLIT-WINDOW-TO-RUN-COMMAND-THEN-EXIT-AFTER","SPLIT-WINDOW","SPLV","SPLVX","SPLX","BG","BGH","BGV","EXITAFTER","PAUSEEITAFTER","STARTAFTER1SECONDPAUSEWITHEXITAFTER","LAUNCH-WITH-TCMD","HELPER-START","HSTART","START-ELEVATED","START-NONELEVATED"]      # ironiCALLy we do not put "CALL" in this list becuase it's hardcoded elsewhere, these are actually call-like things

DEBUG_LOG_EVERY_LINE     = True
DEBUG_FIND_IN_PATH       = False
DEBUG_SHLEX_VALUE_ERR    = False
DEBUG_EXTENSION_CHECKING = False

#PROCESSED_FILES      = set()
PATHS                 = os.getenv("PATH").split(os.pathsep)
bgcolors              = [Back.RED, Back.GREEN, Back.YELLOW, Back.BLUE, Back.MAGENTA, Back.CYAN, Back.WHITE]
fgcolors              = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
#fg_color_cycle       = itertools.cycle(fgcolors)
all_dependencies      = {}
all_called_by         = {}
#FOUND_COMMANDS       = []
DEPENDENCY_NOT_FOUND  = None                              #can change this to a string for internal testing purposes
NOT_PROCESSED         = "{{NOT_PROCESSED}}"               #DO NOT have a space or lowercase be in this!


def remove_redirection_and_piping_from_command(string):
    pattern = r"[\<\>].*$"
    result = re.sub(pattern, "", string)
    return result


def find_in_path(potential_command, raise_if_error=False, while_processing_potential_command=None, recheck_without_parens=False, line=None):
    """
    Find a potential command in system PATH. Return the full command.
    """
    #lobal path, EXECUTABLE_EXTENSIONS, DEBUG_FIND_IN_PATH, DEPENDENCY_NOT_FOUND, NOT_PROCESSED, INTERNAL_COMMANDS #, FOUND_COMMANDS
    global       EXECUTABLE_EXTENSIONS, DEBUG_FIND_IN_PATH, DEPENDENCY_NOT_FOUND, NOT_PROCESSED, INTERNAL_COMMANDS #, FOUND_COMMANDS

    # do not process NOT_PROCESSED - technically it should not even be passed here
    if potential_command == NOT_PROCESSED:
        #logging.debug(f"       {Style.BRIGHT}{Fore.RED}'{potential_command}' is     '{NOT_PROCESSED}'!")
        #logging.debug(f"       {Style.BRIGHT}{Fore.RED}Skipping null command")
        return DEPENDENCY_NOT_FOUND

    #ogging.debug(f"             {Style.BRIGHT}{Fore.RED}'{potential_command}' is NOT '{NOT_PROCESSED}'!")
    logging.debug(f"        {Style.NORMAL}{Fore.YELLOW}.........Checking Path: {potential_command}")

    #if potential_command in FOUND_COMMANDS:
    #    print(f"{Fore.GREEN}We've already found this command before!{Fore.WHITE}")
    #    return

    #otential_command_dirty = potential_command
    potential_command = remove_redirection_and_piping_from_command(potential_command).strip(' ')

    # detect internal commands
    if potential_command.upper() in [NOT_PROCESSED, INTERNAL_COMMANDS]:
        #return f"internal command: {potential_command}"              #this was interesting because it also gave us a list of internal commands. A thought was to maybe store all these as well. But that may be going a bit too far in over-analyzing the situation. Anyway, to do this would require post-processing to sort out the internal commands from the real dependencies, so we decided against this
        return DEPENDENCY_NOT_FOUND


    #if it's explicitly an executable extensions, then we explciitly need it to exist, or throw an error
    _, extension_of_our_command = os.path.splitext(potential_command)
    if extension_of_our_command.upper() in EXECUTABLE_EXTENSIONS: raise_if_error = True

    for path in PATHS:
        claire.tick(mode="fg")
        for ext in [""] + EXECUTABLE_EXTENSIONS:                      #check no-extension because an extension may already be on it!
            #f DEBUG_FIND_IN_PATH: logging.debug(f"\t                 Is {potential_command} in '{path}'?")
            full_path = os.path.join(path, potential_command + ext)
            if DEBUG_FIND_IN_PATH: logging.debug(f"\t                 {full_path} ?")
            if os.path.exists(full_path):
                if DEBUG_FIND_IN_PATH: logging.debug(f"\t                 {Fore.GREEN}exists!: {full_path}{Fore.WHITE}")
                _, extension = os.path.splitext(full_path)            #if it's an executable extensions, then we found it
                extension = extension.lower()
                if DEBUG_FIND_IN_PATH: logging.debug(f"\t                 extension: {extension}")
                if extension.upper() in EXECUTABLE_EXTENSIONS:
                    return full_path.lower()

    # handle parenthesis proceessing if so directed, since sometimes a parenthesis is part of a command name, but sometimes it's part of script structure
    if recheck_without_parens and ('(' in potential_command or ')' in potential_command):
        potential_command_without_parens = potential_command.strip('()')
        found_path = find_in_path(potential_command_without_parens, raise_if_error=raise_if_error, while_processing_potential_command=while_processing_potential_command, recheck_without_parens=False)
        if found_path is not DEPENDENCY_NOT_FOUND: return found_path.lower()

    ## not found in path!
    # at first we wanted to end execution if we encountered something that wasn't in the path:
    # but in fact, if we are in the mode where we process every word and not just the first word - in order to capture ALL Dependencies
    # then a lot of these words are not commands. "Echo Off" for example, "off" is not in path in that is okay.
    # so we should not throw an error if we are processing every line
    if raise_if_error:
        msg = f"\n\n\n{Fore.RED}{Style.BRIGHT}FATAL ERROR: NOT IN PATH: {Style.NORMAL}{potential_command}"
        if potential_command.upper() in INTERNAL_COMMANDS: msg += f" {Fore.MAGENTA}{Back.LIGHTBLACK_EX}because it is an internal command{Back.BLACK}{Fore.WHITE}{Style.RESET_ALL}"
        if while_processing_potential_command: msg += f"\n\twhile processing: {while_processing_potential_command}"
        if line: msg += f" [line {line}]"
        msg += f"\n\n{Fore.MAGENTA}--> Try executing the command '{potential_command}' to see if it is a valid command{Style.RESET_ALL}"
        raise FileNotFoundError(msg)
    return DEPENDENCY_NOT_FOUND



def shlex_safe_split(line):
    """Safely split the line using shlex but fall back to a regular split if that fails."""
    global DEBUG_SHLEX_VALUE_ERR
    lexer = shlex.shlex(line, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ''

    try:
        return shlex.split(line)
    except ValueError as value_error:
        if DEBUG_SHLEX_VALUE_ERR:
            print(f"Error in shlex.split: {str(value_error)}")
            print(f"Falling back to split. Line: {line}")
        try:
            lexer = shlex.shlex(line, posix=False)
            lexer.whitespace_split = True
            lexer.commenters = ''
            return list(lexer)
        except ValueError as value_error_exception:
            if DEBUG_SHLEX_VALUE_ERR:
                print(f"Error in shlex lexer: {str(value_error_exception)}")
                print(f"Falling back to regular split. Line: {line}")
            return line.split()










def get_lines_from_file(script_to_process):
    global SKIP_ARGUMENT_PROCESSING_OF_THESE_COMMANDS, CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER, COMMAND_SEPARATORS, NOT_PROCESSED  # = ["^", "%+"]

    with open(script_to_process, "r", encoding="utf-8") as file:
        lines = file.readlines()

    preprocessed_lines = []

    for line in lines:
        #ine = line.rstrip()                                                                                # Remove trailing whitespaces
        line = line.rstrip().lstrip('@').rstrip('.')

        #or command in SKIP_ARGUMENT_PROCESSING_OF_THESE_COMMANDS:
        #   #f line.lower().lstrip('@').rstrip('.').startswith(("rem ", "echo ")):                                          # Check if line starts with "rem " or "echo "
        #   if line.upper().lstrip('@').rstrip('.').startswith(command+ " "     ):
        #       line = line.split(maxsplit=1)[0] + " " + NOT_PROCESSED                                                      # Keep the command but replace the rest with NOT_PROCESSED
        #   elif line.startswith(":") and len(line.strip()) > 1:                                                            # Check if line starts with ":" and has more than one non-whitespace character
        #       line = ":" + " " + NOT_PROCESSED                                                                            # Keep the ":" but replace the rest with NOT_PROCESSED

        for command in SKIP_ARGUMENT_PROCESSING_OF_THESE_COMMANDS:
            if line.startswith(command + " "):
                line = command + " " + NOT_PROCESSED
                break                                                                                                       # if the line starts with one of the commands, we stop the loop as we've already processed it

            if line.startswith(":") or line.startswith("%"):
                line = f"REM Not processing: {line}"
                break


            if line.upper().startswith("CALL "):                                                                            # check if line starts with "call "
                #arts = line.split(maxsplit=2)                                                                              # split by whitespace into at least 3 parts: "call", the next command, and the rest
                #f len(parts) > 2:                                                                                          # check if there is a next command and a rest part
                #   line = parts[0] + " " + parts[1] + " " + NOT_PROCESSED
                #   break                                                                                                   # stop the loop, we've processed this line
                #arts = line .split     (maxsplit=4)                                                                        # DEBUG: print(f"********** parts[sp] are {parts}")
                parts = shlex.split     (line)
                #parts = shlex_safe_split(line)
                parts = ['"{}"'.format(part) if ' ' in part else part for part in parts]                                    # pylint: disable=C0209

                #DEBUG: print(f"********** parts[sh] are {parts} [length={len(parts)}][p1?{parts[1].upper() in CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER}][p2?{parts[2].upper() in CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER}]")
                if len(parts) > 2:                                                                                          # check if there is a next command and a rest part
                    if   parts[1].upper() in CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER and parts[2].upper() in CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER and len(parts) > 3:           # handle the special case for "call wrapper"
                        line = parts[0] + " " + parts[1] + " " + parts[2] + " " + parts[3] + " " + NOT_PROCESSED
                    elif parts[1].upper() in CALL_COMMANDS_NEEDING_VALIDATION_OF_2ND_PARAMETER and len(parts) > 2:           # handle the special case for "call wrapper"
                        line = parts[0] + " " + parts[1] + " " + parts[2] + " "                  + NOT_PROCESSED
                    else: line = parts[0] + " " + parts[1] + " "                                   + NOT_PROCESSED
                    break                                                                                                    # stop the loop, we've processed this line


        line = re.sub(r'%@\w+\[.*?\]', NOT_PROCESSED, line)                                                 # Process function calls

        if any(separator in line for separator in COMMAND_SEPARATORS):                                      # Check for command separators
            for separator in COMMAND_SEPARATORS:
                line_parts = line.split(separator)
                if len(line_parts) > 1:                                                                     # Here we want to add each part as a separate line in the preprocessed_lines list
                    for part in line_parts: preprocessed_lines.append(part + "\n")                          # Add the line part as a separate line with a newline character
        else:
            preprocessed_lines.append(line)                                                                 # No command separator found, add to current lines

    preprocessed_lines = [line for lines in preprocessed_lines for line in lines.split("\n")]               # Split the lines again in case lines are joined

    return preprocessed_lines









def extract_dependencies(args, level=1, parent=None, script_to_process=None, processed_commands=None, processed_files=None):
    """Extract dependencies from a script."""
    global DEBUG_LOG_EVERY_LINE, DEBUG_EXTENSION_CHECKING, all_dependencies, all_called_by #, PROCESSED_FILES

    dependencies                        = []
    first_level_dependencies            = []
    called_by                           = []


    #DEBUG not processing same file more than once: logging.debug(f"if script_to_process={script_to_process} not in PROCESSED_FILES={PROCESSED_FILES} then PROCESSED_FILES.append({script_to_process})")
    #f script_to_process not in PROCESSED_FILES: PROCESSED_FILES.append(script_to_process)
    if script_to_process not in processed_files: processed_files.add(script_to_process)
    else:                                        return dependencies, first_level_dependencies, all_dependencies, called_by, all_called_by, processed_commands, processed_files


    debug_bgcolor = bgcolors[(5+(level-1)) % len(bgcolors)]      #5=cyan    #pylint:disable=W0612
    logging.debug(f"\n\n{debug_bgcolor}{Fore.BLACK}************************** Processing file: {script_to_process} **************************{Fore.WHITE}{Back.BLACK}")


    lines = get_lines_from_file(script_to_process)


    all_called_by[script_to_process]    = []
    all_dependencies[script_to_process] = {"level": level, "called_by": [parent.lower()] if parent else [], "dependencies": []}

    last_command_was_start_or_call = False                                                             # used in for loop
    line_number = 0
    for line in lines:
        line_number += 1
        line = line.strip()
        line4print = line
        if line4print == "": line4print = '""'
        if DEBUG_LOG_EVERY_LINE:
            if line4print == '""':
                logging.debug("")
            else:
                logging.debug(f"{Fore.CYAN}{Style.BRIGHT}* Processing line: {Style.NORMAL}{line4print}{Fore.WHITE}")

        # If line is a comment or empty, skip the rest of the loop
        if line.upper().startswith("REM") or line.startswith(":") or line.startswith("http") or not line: continue             # skip comments/labels

        line  = line.replace("\\", "\\\\")                                                          # stop shlex complaining but TODO it may be we need to check for a \ not followed by another \ and not so-blindly subdstitute as we're doing here. Think about this later.
        words = shlex_safe_split(line)                                                              # split line into commands/words

        ### note that we're doing things 2 different ways during development: BEGIN
        #check_all_words = False                                                                    # use first words only
        #raise_error_if_not_found_in_path = True                                                    # use first words only
        #if words and not words[0].startswith((":","%",r"/")):                                      # use first words only
        #check_all_words = True                                                                     # check all words
        raise_error_if_not_found_in_path = False                                                    # check all words
        for word_number, potential_command in enumerate(words):                                     # check all words
            continue_after_message = False
            if potential_command not in processed_commands:
                msg_color  = f"{Fore.YELLOW}"
                type_color = f"{Fore.BLACK}{Back.YELLOW}{Style.NORMAL}"
                msg_type   =  "[new!]"
                msg_type_2 =   "new"
                processed_commands.add(potential_command)
            else:
                msg_color  = f"{Fore.RED}"
                type_color = f"{Fore.RED}{Style.BRIGHT}"
                msg_type   =  "[old!]"
                msg_type_2 =   "old"
                continue_after_message = True
            msg = f"{msg_color}      - Processing {msg_type_2} word #{word_number}: {potential_command}    {type_color}{msg_type}{Style.RESET_ALL} "            #"processing new word #1"
            logging.debug(msg)
            if continue_after_message: continue


            is_command = True                                                                       # figure out if we're dealing with a command or not
            potential_command = words[word_number]
            potential_command = potential_command.lstrip('@*"')                                     # "echo" can have be "echo." but that's such a glaring exception that we added 'echo.' to our internal commands ; any command can be "*command" to re-route around aliases ; echo is off if command starts with "@" ; peel off quotes - do NOT do strip('(').strip(')') because BAT files and other commands can in fact have parenthesis in them, and we have some

            current_command_is_start_or_call = False                                                # start/call are special commands
            if potential_command.upper() in ["START", "CALL"]:                                      # if we are dealing with start/call, the actual command is the next part
                current_command_is_start_or_call = True
                if len(words) == word_number: raise ValueError("looks like this line of script has a start/call but no command after it, which would be a syntax error")
                potential_command = words[word_number+1]

            if potential_command in ['(',')']  or '=' in potential_command: is_command = False     #ignore parens which are code structure and not commands, or things like PATH=$P$G [if an equal is in the middle of it, it's not a command]
            if potential_command.startswith(('%', ':', '-', '/')):          is_command = False     #ignore environment variables, labels, command line options

            # note: skipping this means we do not update the last_command_was_start_or_call unless it was actually a commmand
            if not is_command: continue                                                             # skip if this doesn't seem like a command

            # check if our command is internal or not, and if not, find it in the path
            file = ""
            potential_command = potential_command.strip('|')
            if potential_command.upper().strip('()') in INTERNAL_COMMANDS:                                          # skip internal commands
                is_internal_command = True
                logging.debug(f"\t                             {Fore.GREEN}{Style.BRIGHT}{Back.BLUE}{potential_command}=internal command{Style.NORMAL}{Fore.BLACK}{Back.BLACK}")
            else:
                is_internal_command = False
                logging.debug(f"{Fore.YELLOW}        ....potential command?: {potential_command}{Fore.CYAN}\t[Word #{word_number}]{Fore.WHITE}")
                raise_error_if_not_found_in_path = bool(word_number==0 or last_command_was_start_or_call)           # we need a more strict check if we are more sure this is an actual command

                # decide if we are going to search our path for the command or not
                do_find_in_path = True

                # don't process null commands
                if potential_command == NOT_PROCESSED: do_find_in_path = False

                # check if the command is a valid file in the current directory, and if so, don't bother checking path because it's a direct command not relying on our path
                temp_checked=[]
                for ext in [""] + EXECUTABLE_EXTENSIONS:
                    potential_file = potential_command + ext.lower()                                        #DEBUG: print(f"checking if it's {potential_file}")
                    if potential_file not in temp_checked:
                        if os.path.isfile(potential_file):
                            file = os.path.abspath(potential_file)
                            do_find_in_path = False
                        temp_checked.append(potential_file)

                # go ahead and find it in our path if it's a command that relies on our path to be found
                if do_find_in_path:
                    file = find_in_path(potential_command,raise_if_error=raise_error_if_not_found_in_path,while_processing_potential_command=script_to_process,recheck_without_parens=True,line=line_number)    # find the command in our path


            if is_internal_command: continue                                                        # skip internal commands


            # at this point, it is not an internal command, and we have our full filename, and we can add our newly-found dependency


            if file and file in processed_files:
                logging.debug(f"{Fore.YELLOW} * Already processed file: {file}{Fore.WHITE}")
            if file and file not in processed_files:                                                # only process each file 1X
                logging.debug(f"             {Back.GREEN}{Fore.BLACK}Dependency:{Fore.GREEN}{Back.BLACK} {file} {Fore.LIGHTBLACK_EX}(for {script_to_process}){Fore.WHITE}")

                #dependencies.append(file)                                                           # add this command as a dependency
                if file.lower() not in dependencies:    # only add to dependencies if not already present
                    dependencies.append(file.lower())   # add this command as a dependency

                #f level == 1:                first_level_dependencies..append(file)                    # add to level 1 dependencies structure
                if level == 1 and file not in first_level_dependencies:
                    first_level_dependencies.append(file) # add to level 1 dependencies structure if not already present


                #all_dependencies[script_to_process]["dependencies"].append(file)                    # add to all dependencies structure
                if file not in all_dependencies[script_to_process]["dependencies"]:
                    all_dependencies[script_to_process]["dependencies"].append(file) # add to all dependencies structure if not already present


                #f file in all_called_by: all_called_by[file].append(script_to_process)
                if file in all_called_by:
                    if script_to_process not in all_called_by[file]:
                        all_called_by[file].append(script_to_process)
                #else:  all_called_by[file] = [script_to_process]
                else:   all_called_by[file] = [script_to_process]

                #PROCESSED_FILES.add(file)

                _, extension = os.path.splitext(file)
                if DEBUG_EXTENSION_CHECKING: logging.debug(f"             {Fore.LIGHTBLACK_EX}{Back.BLACK}Checking if {file} has an extension in {VALIDATABLE_EXTENSIONS}{Style.RESET_ALL}.")
                if extension.upper() in VALIDATABLE_EXTENSIONS:
                    if DEBUG_EXTENSION_CHECKING: logging.debug(f"\t\t\t\t\t\t\t\t\t\t\t{Fore.LIGHTBLACK_EX}{Back.BLACK}it does{Fore.WHITE}{Back.BLACK}")
                    #ep, first_level, deep_dependencies, temp_called_by, all_called_by, processed_commands, processed_files = extract_dependencies(args, level+1, script_to_process, processed_commands=processed_commands, processed_files=processed_files)
                    #logging.debug(f"dep, first_level, deep_dependencies, temp_called_by, all_called_by, _, _ = extract_dependencies(args, level={level+1}, script_to_process={script_to_process}, processed_commands,processed_files)")
                    dep, first_level, deep_dependencies, temp_called_by, all_called_by, _                 , _               = extract_dependencies(args, level+1, parent=script_to_process, script_to_process=file, processed_commands=processed_commands, processed_files=processed_files)
                    #logging.debug(f" ...Got: dep={dep}, first_level={first_level}, deep_dependencies={deep_dependencies}, temp_called_by={temp_called_by}, all_called_by={all_called_by}")

                    called_by.append(temp_called_by)
                    if dep:
                        logging.debug(f"appending {dep} to dependencies: dependencies.append(dep={dep})")
                        dependencies.append(dep)
                    else:
                        logging.debug(f"not appending {dep} to dependencies because it's falsy")
                    first_level_dependencies.append(first_level)
                    all_dependencies.update(deep_dependencies)
                else:
                    if DEBUG_EXTENSION_CHECKING: logging.debug(f"\t\t\t\t\t\t\t\t\t\t\t{Fore.LIGHTBLACK_EX}{Back.BLACK}it does not{Fore.WHITE}{Back.BLACK}")


            # loop cleanup - store these values for next iteration - note that we would only reach this point of code if it's a command, but it's still not necessarily a start/call command
            last_command_was_start_or_call = current_command_is_start_or_call

    logging.debug(f"\n\n{debug_bgcolor}{Fore.BLACK}************************** Done Processing: {script_to_process} **************************{Back.BLACK}{Fore.WHITE}{Back.BLACK}")

    # clean our lists of the value DEPENDENCY_NOT_FOUND which is only meant to be there if it's the sole value in the list
    variables = [dependencies, first_level_dependencies, all_dependencies, called_by, all_called_by]
    for var in variables:
        if '' in var: var.remove('')                                                                          #remove any empty entries
        if isinstance(var, list) and DEPENDENCY_NOT_FOUND in var and len(var) > 1:
            var.remove(DEPENDENCY_NOT_FOUND)

    return dependencies, first_level_dependencies, all_dependencies, called_by, all_called_by, processed_commands, processed_files




def print_report(dependencies, first_level_dependencies, my_all_dependencies, called_by, my_all_called_by, args):
    logging.debug( "\n")
    logging.debug(f"\n{Fore.BLUE  }{Style.NORMAL}******** Final results: #A:                called_by: ********\n\n\t" +                f"{called_by}{Fore.BLACK}")
    logging.debug(f"\n{Fore.BLUE  }{Style.BRIGHT}******** Final results: #B:            all_called_by: ********\n\n\t" +         f"{my_all_called_by}{Fore.BLACK}")
    logging.debug(f"\n{Fore.YELLOW}{Style.NORMAL}******** Final results: #1: first_level_dependencies: ********\n\n\t" + f"{first_level_dependencies}{Fore.BLACK}")
    logging.debug(f"\n{Fore.GREEN }{Style.NORMAL}******** Final results: #2: " +        "dependencies: ********\n\n\t" +             f"{dependencies}{Fore.BLACK}")
    logging.debug(f"\n{Fore.CYAN  }{Style.NORMAL}******** Final results: #3: " +    "all_dependencies: ********\n\n\t" +      f"{my_all_dependencies}{Fore.BLACK}")


    ### give our output
    #f args.first_level: print((' '.join(first_level_dependencies)).lower())      #the pointlessly short list
    if args.first_level: print(          first_level_dependencies  .lower())      #the pointlessly short list
    elif args.all_deep:  print(               my_all_dependencies  .lower())      #the very thorough list
    #lse:                print(                      dependencies  .lower())      #the list we will probably actually use
    else:                print(f"DEPENDENCIES: {dependencies}")      #the list we will probably actually use


def main():
    """Main function."""
    global VALIDATABLE_EXTENSIONS

    ### parameter parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs='?', default=None, help="filename of the script to check dependencies for")
    parser.add_argument("-f", "--first-level", "--first", "--f", "--level1"   , "--l1", "-l1", "--1", "-1", action='store_true',                          help="return only first level dependencies"         )
    parser.add_argument("-a", "--all-deep"   , "--all"  , "--a", "--levelAll" , "--la", "-la",              action='store_true',                          help="return all dependencies with their attributes")
    parser.add_argument("-c", "--check-path" , "--path" , "--c", "--checkPath", "--cp", "-cp", "--p", "-p", action='store'     , dest='command_to_check', help="check path for command"                       )
    parser.add_argument("-v", "--verbose",                                                                  action='store_true',                          help="write log to standard output"                 )
    args = parser.parse_args()
    command_to_check = args.command_to_check                                                                #DEBUG: print (f"command_to_check is {command_to_check}")

    #DEBUG: print(f"Args are {args}")

    ### parameter validation
    if args.filename is None and args.command_to_check is None:
        parser.error("You must provide either a filename or a command to check!")
    if args.filename:
        if not os.path.exists(args.filename): sys.exit(f"File {args.filename} does not exist.")
        _, extension = os.path.splitext(args.filename)
        if extension.upper() not in VALIDATABLE_EXTENSIONS:
            print(f"{Fore.LIGHTRED_EX}Error: Invalid file extension. Allowed extensions are {VALIDATABLE_EXTENSIONS}")
            sys.exit(1)

    ### logging
    log_filename = sys.argv[0].replace(".py", ".log")
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)
    file_handler = logging.FileHandler(log_filename, mode='w')
    #ormatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
    formatter = logging.Formatter(f'{Fore.LIGHTBLACK_EX}{Back.BLACK}%(levelname)s: {Style.RESET_ALL}%(message)s')
    console_handler = logging.StreamHandler()
    file_handler   .setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)
    logging.getLogger('').addHandler(file_handler)
    if args.verbose:
        #DEBUG: print("Setting up verbose mode")  # This will print only if args.verbose is True
        console_handler.setLevel(logging.DEBUG)  # Set handler level to DEBUG if -v flag is provided
    else:
        console_handler.setLevel(logging.INFO)   # Otherwise, set it to INFO

    ### execution: -c mode
    if command_to_check:
        print(find_in_path(command_to_check, raise_if_error=True))
        file_handler.close()
        sys.exit()

    ### execution: normal

    ### do the work & report what happened
    processed_files    = set()
    processed_commands = set()
    my_dependencies             , my_first_level_dependencies, my_all_dependencies, my_called_by, my_all_called_by, _, _ = extract_dependencies(args,script_to_process=args.filename,processed_commands=processed_commands,processed_files=processed_files)
    print_report(my_dependencies, my_first_level_dependencies, my_all_dependencies, my_called_by, my_all_called_by, args)

    ### cleanup
    file_handler.close()
    #claire.strip_ansi_from_file(log_filename)
    claire.tock()


if __name__ == "__main__":
    main()
