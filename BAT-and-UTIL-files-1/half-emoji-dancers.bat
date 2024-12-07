@Echo off

set THE_DANCERS=%@EXECSTR[list-emoji-env-vars-in-one-line]


set DANCE_LENGTH=6


for %%dancer in (%THE_DANCERS%) do ( 
        title %dancer
        call half-emoji-dance %%[%dancer] %dance_length% 
)
