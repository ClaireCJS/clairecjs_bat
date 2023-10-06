@Echo OFF
:((du -ha --max-depth=1)|sort-by-human-readable-size) :2020 had to mysterioualy drop the -a from -ha for some reason
 ((du -h  --max-depth=1)|sort-by-human-readable-size)
