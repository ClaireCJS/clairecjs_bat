@Echo OFF

REM call debug "Setting emojis..."

if "%1" eq "generate"            (fix_unicode_filenames.py script|sort|uniq >%bat%\emoji.env)
if "%1" eq "force"               (goto :Set_Emojis )
if  "1" eq %EMOJIS_HAVE_BEEN_SET (goto :Already_Set)

:Set_Emojis

    set EMOJI_DEVIL_FACE=%@CHAR[55357]%@CHAR[56840]    
                        set DEVIL_FACE=%EMOJI_DEVIL_FACE%
                        set DEVILFACE=%EMOJI_DEVIL_FACE%
                        set DEVIL=%EMOJI_DEVIL_FACE%

    set EMOJI_PARTY_POPPER=%@CHAR[55356]%@CHAR[57225]
                        set PARTY_POPPER=%EMOJI_PARTY_POPPER%
                        set PARTYPOPPER=%PARTY_POPPER%

    set EMOJI_RED_FLAG=%EMOJI_TRIANGULAR_FLAG%
          set RED_FLAG=%EMOJI_TRIANGULAR_FLAG%

    set CALCULATOR=%EMOJI_POCKET_CALCULATOR%



REM Load emojis generated by our script
    REM timer
    set /r c:\bat\emoji.env
    REM timer

rem Corrections from our script...
    set EMOJI_RIGHT_ARROW_BLUE_BOX=%EMOJI_RIGHT_ARROW%
    set EMOJI_RIGHT_ARROW=%@CHAR[11106]%@CHAR[65035]





        set EMOJIS_HAVE_BEEN_SET=1
:Already_Set










