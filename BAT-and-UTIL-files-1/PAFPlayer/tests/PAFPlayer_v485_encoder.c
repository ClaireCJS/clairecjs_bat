/* PAFPlayer V485 fixed-cell artwork delta encoder. No CRT or external DLLs.
   Compile with MSVC x64 /O2 /GS- /LD /link /NOENTRY /NODEFAULTLIB. */
typedef unsigned char byte;
typedef __int64 i64;
static i64 text(byte *out,i64 at,const char *s) {while(*s) out[at++]=(byte)*s++;return at;}
static i64 number(byte *out,i64 at,int v) {
 int d=1;while(v/d>=10)d*=10;
 while(d){out[at++]=(byte)(48+v/d);v%=d;d/=10;}return at;
}
__declspec(dllexport) i64 paf_encode(const byte *cur,const byte *prev,const byte *origins,
 const i64 *lengths,int rows,int width,int origin_stride,byte *out,i64 capacity,int *runs) {
 i64 used=0;int y,x,c,i,first,last,changed;*runs=0;
 if(rows<0||rows>512||width<1||width>4096||origin_stride<1||origin_stride>256)return -1;
 if(capacity<(i64)rows*((i64)width*64+origin_stride+64))return -1;
 for(y=0;y<rows;y++){
  first=width;last=-1;
  for(x=0;x<width;x++){
   i=((y*width)+x)*7;changed=prev==0;
   if(prev)for(c=0;c<7;c++)if(cur[i+c]!=prev[i+c]){changed=1;break;}
   if(changed){if(first==width)first=x;last=x;}
  }
  if(last<0)continue;
  if(lengths[y]<0||lengths[y]>origin_stride)return -1;
  (*runs)++;
  for(i=0;i<lengths[y];i++)out[used++]=origins[y*origin_stride+i];
  used=text(out,used,"\033[");used=number(out,used,first+1);used=text(out,used,"G\033( @");
  for(x=first;x<=last;x++){
   i=(y*width+x)*7;changed=x==first;
   if(!changed)for(c=0;c<6;c++)if(cur[i+c]!=cur[i-7+c]){changed=1;break;}
   if(changed){
    used=text(out,used,"\033[38;2;");
    for(c=0;c<6;c++){
     if(c==3)used=text(out,used,"48;2;");
     used=number(out,used,cur[i+c]);out[used++]=(c==5)?'m':';';
    }
   }
   out[used++]=cur[i+6];
  }
  used=text(out,used,"\033(B\033[0m");
 }
 return used;
}
