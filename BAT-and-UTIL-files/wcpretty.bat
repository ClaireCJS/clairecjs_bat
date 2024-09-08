@Echo OFF

:DESCRIPTION: This is a cosmetic wrapper to wc (unix wordcount util) that prints a header over the numbers, so that we know what they are, then runs wc
:DESCRIPTION: NOTE: The headers don't actually line up perfectly —— that would require postprocessing wc itself to line up the columns
:DESCRIPTION: It takes the same command-line option as wc


call wcheader %*
call wc       %*

