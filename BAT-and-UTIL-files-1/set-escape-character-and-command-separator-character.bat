@Echo OFF            
@on break cancel

setdos /X-8
                set ESCAPE_CHARACTER=`±`
setdos /X0

setdos /X-5
                set COMMAND_SEPARATOR_CHARACTER=^
setdos /X0

                set COMMAND_SEPARATOR=CARET
                
                
