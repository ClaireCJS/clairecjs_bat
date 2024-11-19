@Echo off
@on break cancel


option //unicodeoutput=yes
(type clip: |:u8 call sort ) >clip:
option //unicodeoutput=no

