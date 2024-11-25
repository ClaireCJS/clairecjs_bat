@Echo Off
@on break cancel

rem Start after 1 second pause, with an 'exitafter' parameter afterward
rem [some of our scripts will issue an 'exit' if 'exitafter' is passed or set]

sleep 1
start "%1" %* exitafter
