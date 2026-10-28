/* V519 sparse artwork delta transport. No CRT or external DLL dependencies.
   Full frames retain V486 bytes. Deltas preserve every FG/BG/glyph and row guard. */
typedef unsigned char byte;
typedef __int64 i64;
static i64 text(byte *out,i64 at,const char *s) {while(*s) out[at++]=(byte)*s++;return at;}
static i64 number(byte *out,i64 at,int v) {
 int d=1;while(v/d>=10)d*=10;
 while(d){out[at++]=(byte)(48+v/d);v%=d;d/=10;}return at;
}
static int digits(int v){return v<10?1:(v<100?2:(v<1000?3:4));}
static int differs(const byte *a,const byte *b,int n){int c;if(!b)return 1;for(c=0;c<n;c++)if(a[c]!=b[c])return 1;return 0;}
static int color_cost(const byte *a,const byte *b){
 int fg=differs(a,b,3),bg=differs(a+3,b?b+3:0,3),c,cost=0;
 if(!fg&&!bg)return 0;
 cost=2+(fg?5:0)+(bg?5:0);
 for(c=0;c<6;c++)if((c<3&&fg)||(c>=3&&bg))cost+=digits(a[c])+1;
 return cost;
}
static i64 color(byte *out,i64 at,const byte *a,const byte *b,int legacy){
 int fg=differs(a,b,3),bg=differs(a+3,b?b+3:0,3),c;
 if(!fg&&!bg)return at;
 if(legacy)fg=bg=1;
 at=text(out,at,"\033[");
 if(fg){at=text(out,at,"38;2;");for(c=0;c<3;c++){at=number(out,at,a[c]);out[at++]=(c==2&&!bg)?'m':';';}}
 if(bg){at=text(out,at,"48;2;");for(c=3;c<6;c++){at=number(out,at,a[c]);out[at++]=c==5?'m':';';}}
 return at;
}
__declspec(dllexport) i64 paf_encode(const byte *cur,const byte *prev,const byte *origins,
 const i64 *lengths,int rows,int width,int origin_stride,byte *out,i64 capacity,int *runs) {
 i64 used=0;int y,x,c,i,first,last,end,j,bridge,jump;const byte *a,*b,*active,*candidate;
 if(!cur||!origins||!lengths||!out||!runs)return -1;*runs=0;
 if(rows<0||rows>512||width<1||width>4096||origin_stride<1||origin_stride>256)return -1;
 if(capacity<(i64)rows*((i64)width*64+origin_stride+64))return -1;
 for(y=0;y<rows;y++){
  if(lengths[y]<0||lengths[y]>origin_stride)return -1;
  a=cur+(i64)y*width*7;b=prev?prev+(i64)y*width*7:0;
  first=width;last=-1;
  for(x=0;x<width;x++)if(differs(a+x*7,b?b+x*7:0,7)){if(first==width)first=x;last=x;}
  if(last<0)continue;
  (*runs)++;
  for(i=0;i<lengths[y];i++)out[used++]=origins[y*origin_stride+i];
  used=text(out,used,"\033[");used=number(out,used,first+1);used=text(out,used,"G\033( @");
  active=0;x=first;
  while(x<=last){
   if(b&&!differs(a+x*7,b+x*7,7)){
    end=x+1;while(end<last&&!differs(a+end*7,b+end*7,7))end++;
    /* Compare painting the unchanged bridge with one absolute-column jump.
       Both retain DRCS and the last emitted color. Include next cell's SGR. */
    candidate=active;bridge=0;
    for(j=x;j<=end;j++){bridge+=color_cost(a+j*7,candidate)+1;candidate=a+j*7;}
    jump=3+digits(end+1)+color_cost(a+end*7,active)+1;
    if(jump<bridge){used=text(out,used,"\033[");used=number(out,used,end+1);out[used++]='G';(*runs)++;}
    else for(j=x;j<end;j++){used=color(out,used,a+j*7,active,0);out[used++]=a[j*7+6];active=a+j*7;}
    x=end;
   }
   used=color(out,used,a+x*7,active,b==0);out[used++]=a[x*7+6];active=a+x*7;x++;
  }
  used=text(out,used,"\033(B\033[0m");
 }
 return used;
}

/* Fused luma composition. All arithmetic is double with explicit round-to-even;
   no /fp:fast, FMA contraction, lookup quantization or image-quality reduction. */
static int even_round(double v) {
 int n=(int)v; double f=v-n;
 if(f>0.5 || (f==0.5 && (n&1))) n++;
 if(f< -0.5 || (f== -0.5 && (n&1))) n--;
 return n;
}
static int clipped(int v) {return v<0?0:(v>255?255:v);}
static void luma_color(const int *base,double coefficient,double strength,int opacity,int tall,int *result) {
 int c,peak=base[0],target,mixed;
 if(base[1]>peak)peak=base[1];if(base[2]>peak)peak=base[2];
 for(c=0;c<3;c++){
  target=coefficient>=0?even_round(base[c]+(255-base[c])*coefficient):
   (base[c]==peak?base[c]:even_round(base[c]*(-coefficient)));
  mixed=clipped(even_round(base[c]+(target-base[c])*strength));
  if(opacity)mixed=even_round((mixed*(1000-opacity)+base[c]*opacity)/1000.0);
  if(tall)mixed=clipped(even_round(mixed/32.0)*32);
  result[c]=mixed;
 }
}
__declspec(dllexport) int paf_compose_luma(
 const double *half_coeff,const double *bar_coeff,const byte *background,
 const byte *empty_cells,const byte *bar_glyphs,const byte *base_colors,
 const int *edges,const byte *table,int rows,int width,int first_row,int tall,
 double strength,int opacity,byte *out,i64 capacity) {
 int y,x,c,i,j,ll,rl,lw,rw,le,re,denom,base[3],left[3],right[3],color[3];
 if(rows<1||rows>512||width<1||width>4096||opacity<0||opacity>1000||strength<0||strength>1)return -1;
 if(capacity<(i64)rows*width*7)return -1;
 for(y=0;y<rows;y++)for(x=0;x<width;x++){
  i=(y*width+x)*7;j=(y*width+x)*2;
  ll=(y+first_row>edges[x*4])?8:((y+first_row<edges[x*4])?0:edges[x*4+1]);
  rl=(y+first_row>edges[x*4+2])?8:((y+first_row<edges[x*4+2])?0:edges[x*4+3]);
  if(ll<0||ll>8||rl<0||rl>8)return -1;
  if(ll==0 && rl==0){for(c=0;c<7;c++)out[i+c]=empty_cells[i+c];continue;}
  if(ll==8 && rl==8){
   for(c=0;c<3;c++)base[c]=even_round((base_colors[x*6+c]+base_colors[x*6+c+3])/2.0);
   luma_color(base,bar_coeff[j],strength,opacity,0,color);
   for(c=0;c<3;c++)out[i+c]=(byte)color[c];
   luma_color(base,bar_coeff[j+1],strength,opacity,0,color);
   for(c=0;c<3;c++)out[i+c+3]=(byte)color[c];
   out[i+6]=bar_glyphs[y*width+x];continue;
  }
  for(c=0;c<3;c++){base[c]=base_colors[x*6+c];left[c]=0;right[c]=0;}
  if(ll)luma_color(base,half_coeff[j],strength,opacity,tall,left);
  for(c=0;c<3;c++)base[c]=base_colors[x*6+c+3];
  if(rl)luma_color(base,half_coeff[j+1],strength,opacity,tall,right);
  lw=ll?ll:1;rw=rl?rl:1;le=8-ll;re=8-rl;denom=le+re;
  for(c=0;c<3;c++){
   out[i+c]=(byte)even_round((left[c]*lw+right[c]*rw)/(double)(lw+rw));
   if(ll==0 && rl>0)out[i+c+3]=background[j*3+c];
   else if(rl==0 && ll>0)out[i+c+3]=background[j*3+c+3];
   else out[i+c+3]=(byte)even_round((background[j*3+c]*le+background[j*3+c+3]*re)/(double)denom);
  }
  out[i+6]=table[ll*9+rl];
 }
 return 0;
}

int _fltused = 0;
