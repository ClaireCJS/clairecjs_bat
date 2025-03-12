@echo off


iff "1" != "%validated_getlyrics_in_path%" then
        if not defined filemask_audio call validate-environment-variable filemask_audio
        call validate-in-path get-lyrics
        set validated_getlyrics_in_path=1
endiff

for %%fil in (%filemask_audio%) do call get-lyrics "%fil"


