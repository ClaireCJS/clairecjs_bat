@on break cancel
@Echo OFF

pushd .
                                 "c:\util2\Milkdrop3\Milkdrop latest\"                        
rem     start    /elevated       "c:\util2\Milkdrop3\MilkDrop latest\MilkDrop 3.exe"
rem    *start    /elevated %@SFN["c:\util2\Milkdrop3\MilkDrop latest\MilkDrop 3.exe"]
       *start "" /elevated %@SFN["c:\util2\Milkdrop3\MilkDrop latest\MilkDrop 3.exe"]
popd

call sleep 1
call fix-minilyrics-window-size-and-position





