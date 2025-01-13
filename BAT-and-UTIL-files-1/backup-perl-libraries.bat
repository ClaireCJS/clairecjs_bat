@loadbtm on
@Echo OFF
on break cancel


rem Validate enviroment once per session:
        iff 1 ne %validated_bkpprllib% then
                call validate-environment-variable PERL_OFFICIAL_SITELIB_ALL python_claire_drive_backup
                call validate-in-path              sync-perlsitelib-to-dropbox.bat sync-a-folder-to-somewhere
                set  validated_bkpprllib=1
        endiff


rem Set folders:
        set SYNCSOURCE=%PERL_OFFICIAL_SITELIB_ALL%
        set SYNCBASE=%python_claire_drive_backup%:\backups\clairecjs-official-perl-site-lib\

rem Make sure destination folders exist:
    if not isdir %SYNCBASE% (md /s %SYNCBASE%)
    call yyyymmdd
    set SYNCTARGET=%SYNCBASE%\%YYYY%%MM%-%MACHINENAME%
    if not isdir %SYNCTARGET% (md /s %SYNCTARGET%)
    (call sync-a-folder-to-somewhere) |:u8 fast_cat



rem It's nice to also do this, simply because this already exists...
rem ...but let's not do it if we're currently running our autoexec.bat
        rem if 1 ne %AUTOEXEC% (call sync-perlsitelib-to-dropbox.bat)


