@Echo OFF



:: This was never developed. Seems like it might actually be easier to write a Perl script that just outputs ANSI. BAH!

:BAH!: set h=%@fileopen[" \\.\pipe\",r]
:BAH!: echo * reading %@saferead[%h]
:BAH!: echo * closing handle #%h: %@fileclose[%h]

                

                if "%@REGEX[FIRE,%DESC%]"    eq "1"  color      yellow    on black
				if "%@REGEX[HADES,%DESC%]"   eq "1"  color        red     on black
				if "%@REGEX[THAILOG,%DESC%]" eq "1"  color bright red     on black
				if "%@REGEX[GOLIATH,%DESC%]" eq "1"  color        magenta on black
