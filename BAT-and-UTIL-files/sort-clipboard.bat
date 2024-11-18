@Echo off


option //unicodeoutput=yes
(type clip: |:u8 call sort ) >clip:
option //unicodeoutput=no

