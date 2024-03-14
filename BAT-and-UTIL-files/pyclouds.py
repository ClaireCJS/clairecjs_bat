#!/usr/bin/python

# This software is distributed under the GPL, version 2.
# inspired by the clouds at peffis.com, http://peffis.com/clouds.php
# Requires the Python Imaging Library (PIL) http://www.pythonware.com/products/pil/


# usage:
# ./pyclouds.py <width> <height> [ list of photos to include in the cloud ]
# I like to run it like
# ./pyclouds.py 1600 1200 `find /path/to/photos -name '*.jpg'`
# echo %@EXECSTR[(dir/b *.jpg|convert-newlines-to-spaces)]
# set TEST=%@EXECSTR[(dir/b *.jpg|convert-newlines-to-spaces)]
# c:pyclouds.py 1024 768 %TEST

# version 0.1
# TODO:
#   -- fix the plasma generator (grid lines) and speed it up
#   -- add better command line processing, or perhaps a UI of some kind (file display)
#      -- save to something other than cloud.png
#   -- show cloud while being built
#   -- randomize insertion order of the images passed in

# basic algorithm
# take a large collection of images.
#  pre analyze them? to find a good target size, perhaps take a command line argument
# create a blank image of that size (white.)
# for each image, chosen in some order 
#    pick a random spot to place it on the target image (possibly scaling.)
#    create a mask for it using the midpoint whatsit algorithm
#    paste it into the final image using the above as alpha
#    ...
#    profit!

from random import *
import os, sys
#import PIL
#from PIL import Image
#from PIL 
import Image
import ImageColor

# command line args

#(scratch, height,width,imgh,imgw,dir) = sys.argv
(width,height) = (sys.argv[1], sys.argv[2])

class PlasmaGenerator:
   def __init__(self):
      self.cache = {}
      self.plasmacount = 0
      
   def limit(self, num):
      if(num > 255):
        return 255
      if(num < 0):
        return 0
      return num


   def newPlasma(self,(width, height)): #TODO GOAT OH OH OH
   #def newPlasma(width, height):	#runtime error!
      if(self.cache.has_key((width,height))):
         # we have a cached plasma in this size. To use or generate new, that is the question.
         # odds of making new = 1/<cached count> 
         if(randint(0,len(self.cache[(width,height)])) == 0): # generate new
            sys.stdout.write("   Generating new plasma")
            self.height = (height/2)
            self.width = (width/2)
            self.im = Image.new('L', (self.width,self.height), 0)
            self.make_plasma(255*2, 0, 0, (self.width-1), (self.height-1), 0, 0, 0, 0, 0)  
            self.im = self.im.resize((width,height), Image.ANTIALIAS)
            self.cache[(width,height)].append(self.im)
            self.im.save("plasma-%d.png"%self.plasmacount, 'PNG')
            self.plasmacount += 1
            return self.im
         else:
            # return a random one from the cached list
            cached = randint(0,len(self.cache[(width,height)])-1)
            sys.stdout.write("   Using cached plasma %d" %cached)
            return self.cache[(width,height)][cached]
      else:
         sys.stdout.write("   Generating new plasma")
         self.height = (height/2)
         self.width = (width/2)
         self.im = Image.new('L', (self.width,self.height), 0)
         self.make_plasma(255*2, 0, 0, (self.width-1), (self.height-1), 0, 0, 0, 0, 0)  
         self.im = self.im.resize((width,height), Image.ANTIALIAS)
         self.cache[(width,height)] = [self.im]
         self.im.save("plasma-%d.png"%self.plasmacount, 'PNG')
         self.plasmacount += 1
         return self.im


   # TODO: optimize the snot out of this. It'd be really easy to make iterative
   # with a stack (push on the sub-rectangles as you go.) 4-way recursive branching == slow
   # also, randomize subdivisions? something is making a grid pattern appear on the clouds. 
   def make_plasma(self, scaling, x0, y0, x1, y1, tr, tl, br, bl, depth):
      # I suspect this is overprinting, but we'll let it slide for now
      if((x1-x0)<=1 and (y1-y0)<=1):
         if(x0 >= self.width):
            return
         if(x1 >= self.width):
            return
         if(y0 >= self.height):
            return
         if(y1 >= self.height):
            return
         try:
            self.im.putpixel((x0,y0), tr)
            self.im.putpixel((x0,y1), br)
            self.im.putpixel((x1,y0), tl)
            self.im.putpixel((x1,y1), bl)
         except:
            #print "Error: placing pixels at <%d,%d> and <%d,%d> when height=%d and width=%d"%(x0,y0,x1,y1,self.height,self.width)
            pass

         return
      
      if(x0 == 0):
         l = 0
      else:
         l = (tl/2+bl/2)
      
      if(x1 == self.width-1):
         r = 0
      else:
         r = (tr/2+br/2)

      if(y0 == 0):
         t = 0
      else:
         t = (tl/2+tr/2)

      if(y1 == (self.height-1)):
         b = 0
      else:
         b = (bl/2+br/2)

      c = tr/4 + tl/4 + br/4 + bl/4 + randint(-(scaling/4), scaling)
      c = self.limit(c)

      xm = x0+(x1-x0)/2
      #if((x1-x0)%2):
      #   xm = xm+1
      ym = y0+(y1-y0)/2
      #if((y1-y0)%2):
      #   ym = ym+1
      
      self.make_plasma(scaling/2, x0, y0, xm, ym, t, tl, c, l, depth+1)
      self.make_plasma(scaling/2, xm+1, y0, x1, ym, tr, t, r, c, depth+1)
      self.make_plasma(scaling/2, x0, ym+1, xm, y1, c, l, b, bl, depth+1)
      self.make_plasma(scaling/2, xm+1, ym+1, x1, y1, r, c, br, b, depth+1)   


            

#(scratch, height,width,imgh,imgw,dir) = sys.argv
width=int(width)
height=int(height)
maxwidth=(width*0.45)
maxheight=(height*0.45)

# Build a new image based on the size given on the command line
img = Image.new('RGB', (width,height), '#ffffff')

# by default scale images to .25 width or .25 height, whichever is bigger
# scale them 1:1

p = PlasmaGenerator()

try:
    f = open("imagelist.txt", "r")
    files = f.readlines()
    f.close
    GotFileList = True
except:
    GotFileList = False

#print "files is " + f.printlines()
for f in (files):
  print "* listed:", f,

for f in (files):
   f=f.rstrip()
   print "Trying file \"", f, "\"..."
   try:
      #cl= Image.open(sys.argv[f])
      cl= Image.open(f)
   except:
      print "Hmmm, ", f, "didn't seem to open...."
      continue
   if(cl != None):
      cl.thumbnail((maxwidth,maxheight), Image.ANTIALIAS) #if the image is larger than the max allowable, shrink
      #sys.stdout.write("Adding image %s" %(sys.argv[f]))
      print "Adding image",  f
      mask = p.newPlasma(cl.size)
      img.paste(cl, (randint(-100,width+50), randint(-100,height+50)), mask)

########## copy of previous loop again ##############
for f in (files):
   f=f.rstrip()
   print "Trying file \"", f, "\"..."
   try:
      #cl= Image.open(sys.argv[f])
      cl= Image.open(f)
   except:
      print "Hmmm, ", f, "didn't seem to open...."
      continue
   if(cl != None):
      cl.thumbnail((maxwidth,maxheight), Image.ANTIALIAS) #if the image is larger than the max allowable, shrink
      #sys.stdout.write("Adding image %s" %(sys.argv[f]))
      print "Adding image",  f
      mask = p.newPlasma(cl.size)
      img.paste(cl, (randint(-100,width+50), randint(-100,height+50)), mask)
########## copy of previous loop again ##############

img.save("cloud.png", "PNG")
