@Echo OFF
 on break cancel

    set NATURE=age

::::: GET START DATE FROM WORD PARAMETER:  (i.e. "Claire")

                            set START_DATE_YYYYMMDD=19740113


    if "%1" eq "Mom"       (set START_DATE_YYYYMMDD=19470402 %+ goto :Go )
    if "%1" eq "Dad"       (set START_DATE_YYYYMMDD=19480301 %+ goto :Go )
    if "%1" eq "Claire"    (set START_DATE_YYYYMMDD=19740113 %+ goto :Go )
    if "%1" eq "Clio"      (set START_DATE_YYYYMMDD=19740113 %+ goto :Go )
    if "%1" eq "Carolyn"   (set START_DATE_YYYYMMDD=19760223 %+ goto :Go )
    if "%1" eq "Beth"      (set START_DATE_YYYYMMDD=19770612 %+ goto :Go )
    if "%1" eq "Britt"     (set START_DATE_YYYYMMDD=19790630 %+ goto :Go )
    if "%1" eq "Marceline" (set START_DATE_YYYYMMDD=19980815 %+ goto :Go )
    if "%1" eq "Marcy"     (set START_DATE_YYYYMMDD=19980815 %+ goto :Go )


    :DEBUG: echo are we here %1


::::: OR GET IT FROM NUMERIC PARAMETER:  (i.e. "19991231")

    if "%1" ne ""          (set START_DATE_YYYYMMDD=%1       %+ goto :Go)





:Go
    call display-time-elapsed 

