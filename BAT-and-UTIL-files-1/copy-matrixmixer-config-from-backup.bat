@Echo OFF



rem COPY OUR MATRIXMIXER CONFIG FROM OUR BACKUP:
    pushd
        call appdata 
        cd   winamp
        call warning_soft "MatrixMixer configuration re-copied" silent
        echo ry | *copy /z out_mixer.ini.official out_mixer.ini    
    popd


