@Echo OFF

:DESCRIPTION: Puts us in sleeping mode, so noises are visual instead of audio, to not wake up spouse! Use 'awake' to undo.
 
 
 set SLEEPING=1


rem Old X10 home automation lighting stuff that doesn't apply anymore:
        if 1 ne %X10_DOWN (call B1 OFF)




call advice "Mode set to SLEEPING / QUIET / SLEEPING SPOUSE.  To undo, run 'awake'"

