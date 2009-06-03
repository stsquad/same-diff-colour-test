#!/usr/bin/env python

"""

An attempt to interface directly to the Visage VSG DLL library and wrap
it up in a python class. This is so I can attempt to get the sameDiffColorsHSL
experiment working with minimum hackage

The DLL thunking is all handled by the ctypes package

"""

import sys
from ctypes import *

# Constants
vsgVIDEOPAGE=256;

# colour space
vsgCS_CIE1931            = 0 # 1931 CIE, x,y,luminance 
vsgCS_DKLPolar1984       = 1 # Derrington, Krauskopf, Lennie 
vsgCS_HSV                = 2 # Hue, saturation, value 
vsgCS_RGB                = 3 # RGB colour in range 0..1 
vsgCS_SML                = 4 # S,M,L cones on separate axes 
vsgCS_CIE1976            = 5 # 1976 CIE u',v',luminance 
vsgCS_MacLeodBoynton1979 = 6 # Constant S, M&L and Luminance 
vsgCS_RGBDAC             = 7 # RGB Space converted into DAC range 

# The vsgTrivial contains 3 values. By default this maps onto RGB
# but (we think?) this can be changed with vsgChangeColorSpace

class vsgTRIVIAL(Structure):
    _fields_ = [ ("a", c_double),
                 ("b", c_double),
                 ("c", c_double) ]
    
class PyVSG:

    """
    Boiler plate stuff to load the DLL
    """
    def __init__(self):

        self.current_pen = 0
        
        if sys.platform == 'win32':
            print "Loading VSGDLL"
            self.vsgDll = windll.LoadLibrary("VSGV8.DLL")
            n = c_int(1)
            result = self.vsgDll.vsgInit('')
            if result < 0:
                print "Houston we have a problem"
            else:
                self.active = True
                self.height = self.vsgDll.vsgGetScreenHeightPixels()
                self.width = self.vsgDll.vsgGetScreenWidthPixels()
                self.vsgDll.vsgSetDrawPage(vsgVIDEOPAGE, 0, 0)
                print "Cool, we seems to have a %dx%d screen" % (self.height, self.width)
        else:
            # Don't do the calls, but do fake things
            self.active = False
            self.height = 400
            self.width  = 600
            print "Not on Windows, we shall fake the VSG calls"
        

    """
    Set the display page
    """
    def vsgSetDisplayPage(self, page):
        if self.active:
            res = self.vsgDll.vsgSetDisplayPage(page)
            if res < 0:
                print "vsgSetDisplayPage failed"
    

    """
    Set the current drawing page, by default switching to a draw page
    clears it.
    """
    def vsgSetDrawPage(self, page, clear=True):
        if self.active:
            res = self.vsgDll.vsgSetDrawPage(c_ulong(vsgVIDEOPAGE), c_ulong(page), c_ulong(0))
            self.current_pen = 0
            if res < 0:
                print "vsgSetDrawPage failed"

    """
    Set the colour space of the visage system
    """
    def vsgSetColourSpace(self, colour):
        if self.active:
            res = self.vsgDll.vsgSetColourSpace(c_ulong(colour))
            if res < 0:
                print "vsgSetColourSpace failed"

    def vsgSpaceToSpace(self, srcSpace, srcColour, dstSpace, maximise=False):
        dstColour = vsgTRIVIAL()

        # I miss the ternary operator
        if maximise == True:
            maxval = 1
        else:
            maxval = 0
            
        if self.active:
            res = self.vsgDll.vsgSpaceToSpace(c_ulong(srcSpace), pointer(srcColour), c_ulong(dstSpace), pointer(dstColour), c_ulong(maxval))
            if res < 0:
                print "vsgSpaceToSpace failed"
#            else:
#                print "vsgSpaceToSpace gives (%f,%f,%f)" % (dstColour.a, dstColour.b, dstColour.c)
        else:
            print "vsgSetColourSpace can't work"
        return dstColour

    """
    Set the colour index n to colour
    """
    def vsgPaletteSet(self, index, colour):
        if self.active:
            res = self.vsgDll.vsgPaletteSet(index, index, pointer(colour))
            if res < 0:
                print "vsgPaletteSet failed :-("

    """
    Select the drawing pen
    """
    def vsgSetPen1(self, index):
        if self.active:
            res = self.vsgDll.vsgSetPen1(index)
            if res < 0:
                print "vsgSetPen failed :-("

    """
    Set the draing pen to the next colour

    This auto increments the current_pen. If you do too many we will run
    out of pallete entries. Each time the screen is cleared (setDrawPage)
    we reset the pen to 0
    
    """
    def vsgSetDrawColour(self, colour):
        if self.active:
            self.current_pen = self.current_pen+1
            self.vsgPaletteSet(self.current_pen, colour)
            self.vsgSetPen1(self.current_pen)
            print "Current pen is %d (%f, %f, %f)" % (self.current_pen, colour.a, colour.b, colour.c)
                
    """
    Draw a rectangle
    """
    def vsgDrawRect(self, x, y, width, height):
        if self.active:
            res = self.vsgDll.vsgDrawRect(c_double(x),
                                          c_double(y),
                                          c_double(width),
                                          c_double(height))
            if res < 0:
                print "vsgDrawRect failed"
            

        

"""
Test code

Initialise the display and draw a red square (exactly like
the example MATLAB code Simple Square)
"""

if __name__ == "__main__":
    import time
    
    vsg = PyVSG()

    # show page 1, draw on 0
    vsg.vsgSetDrawPage(1)
    vsg.vsgSetDisplayPage(0)

    #
    # Draw a set of concentrice boxes of darker
    # reds
    #
    red = vsgTRIVIAL(1.0, 0.0, 0.0)
    vsg.vsgPaletteSet(1, red)
    vsg.vsgSetPen1(1)
    vsg.vsgDrawRect(0,0,vsg.height/2, vsg.height/2)

    size = vsg.height/2
    index = 1;
    while index<255:
         index = index + 1
         red.a = red.a*0.95
         size = size * 0.95
         vsg.vsgPaletteSet(index, red)
         vsg.vsgSetPen1(index)
         vsg.vsgDrawRect(0,0,size,size)

    # And now switch to page 0
    vsg.vsgSetDisplayPage(1)

    # sleep for a bit
    print "Sleeping a bit"
    time.sleep(5)

    print "Switching CIE1976 Colour Space"
    vsg.vsgSetColourSpace(vsgCS_CIE1976)
    vsg.vsgSetDrawPage(0)
    
    # According to wikipedia L=0..100 u,v=+/-100 but I'm sticking with float
    # the initial lab colours are generated from http://www.brucelindbloom.com/index.html?ColorCalcHelp.html
    # but some turn out wierd. The second inner box is then drawn with the
    # colour generated by using the visage colour space conversion function
    
    step = 20

    # Red
    labRed = vsgTRIVIAL(50.885508, 55.425972, 26.775870)
    vsg.vsgPaletteSet(1, labRed)
    vsg.vsgSetDrawColour(labRed)
    vsg.vsgDrawRect(0,0,vsg.height/2, vsg.height/2)

    rgbRed = vsgTRIVIAL(1.0, 0.0, 0.0)
    labRed = vsg.vsgSpaceToSpace(vsgCS_RGB, rgbRed, vsgCS_CIE1976)
    vsg.vsgSetDrawColour(labRed)
    vsg.vsgDrawRect(0,0,vsg.height/2 - step, vsg.height/2 - step)

    # Green
    labGreen = vsgTRIVIAL(49.653405, -37.918696, 11.629321)
    vsg.vsgSetDrawColour(labGreen)
    vsg.vsgDrawRect(0,0,vsg.height/3, vsg.height/3)

    rgbGreen = vsgTRIVIAL(0.0, 1.0, 0.0)
    labGreen = vsg.vsgSpaceToSpace(vsgCS_RGB, rgbGreen, vsgCS_CIE1976)
    vsg.vsgSetDrawColour(labGreen)
    vsg.vsgDrawRect(0,0,vsg.height/3 - step, vsg.height/3 - step)
    
    # Blue
    labBlue = vsgTRIVIAL(42.823454, -21.589634, -24.771455)
    vsg.vsgSetDrawColour(labBlue)
    vsg.vsgDrawRect(0,0,vsg.height/4, vsg.height/4)

    rgbBlue = vsgTRIVIAL(0.0, 0.0, 1.0)
    labBlue = vsg.vsgSpaceToSpace(vsgCS_RGB, rgbBlue, vsgCS_CIE1976)
    vsg.vsgSetDrawColour(labBlue)
    vsg.vsgDrawRect(0,0,vsg.height/4 - step , vsg.height/4 - step)

    rgbBlue = vsgTRIVIAL(0.0, 0.0, 0.9)
    labBlue = vsg.vsgSpaceToSpace(vsgCS_RGB, rgbBlue, vsgCS_CIE1976)
    vsg.vsgSetDrawColour(labBlue)
    vsg.vsgDrawRect(0,0,vsg.height/4 - step , vsg.height/4 - step)

    gbBlue = vsgTRIVIAL(0.0, 0.0, 0.8)
    labBlue = vsg.vsgSpaceToSpace(vsgCS_RGB, rgbBlue, vsgCS_CIE1976)
    vsg.vsgSetDrawColour(labBlue)
    vsg.vsgDrawRect(0,0,vsg.height/4 - step , vsg.height/4 - step)

    gbBlue = vsgTRIVIAL(0.0, 0.0, 0.7)
    labBlue = vsg.vsgSpaceToSpace(vsgCS_RGB, rgbBlue, vsgCS_CIE1976)
    vsg.vsgSetDrawColour(labBlue)
    vsg.vsgDrawRect(0,0,vsg.height/4 - step , vsg.height/4 - step)

    vsg.vsgSetDisplayPage(0)
    
    
    
        
    

