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
        print "Loading VSGDLL"
        self.vsgDll = windll.LoadLibrary("VSGV8.DLL")
        n = c_int(1)
        result = self.vsgDll.vsgInit('')
        if result < 0:
            print "Houston we have a problem"
        else:
            self.height = self.vsgDll.vsgGetScreenHeightPixels()
            self.width = self.vsgDll.vsgGetScreenWidthPixels()
            self.vsgDll.vsgSetDrawPage(vsgVIDEOPAGE, 0, 0)
            print "Cool, we seems to have a %dx%d screen" % (self.height, self.width)

    """
    Set the display page
    """
    def vsgSetDisplayPage(self, page):
        res = self.vsgDll.vsgSetDisplayPage(page)
        if res < 0:
            print "vsgSetDisplayPage failed"
    

    """
    Set the current drawing page, by default switching to a draw page
    clears it.
    """
    def vsgSetDrawPage(self, page, clear=True):
        res = self.vsgDll.vsgSetDrawPage(c_ulong(vsgVIDEOPAGE), c_ulong(page), c_ulong(0))
        if res < 0:
            print "vsgSetDrawPage failed"

    """
    Set the colour space of the visage system
    """
    def vsgSetColourSpace(self, colour):
        res = self.vsgDll.vsgSetColourSpace(c_ulong(colour))
        if res < 0:
            print "vsgSetColourSpace failed"

    """
    Set the colour index n to colour
    """
    def vsgPaletteSet(self, index, colour):
        res = self.vsgDll.vsgPaletteSet(index, index, pointer(colour))
        if res < 0:
            print "vsgPaletteSet failed :-("

    """
    Select the drawing pen
    """
    def vsgSetPen1(self, index):
        res = self.vsgDll.vsgSetPen1(index)
        if res < 0:
            print "vsgSetPen failed :-("


    """
    Draw a rectangle
    """
    def vsgDrawRect(self, x, y, width, height):
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
    
    red = vsgTRIVIAL(1.0, 0, 0)
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

    print "Switching colour space"
    vsg.vsgSetColourSpace(vsgCS_CIE1976)
    # According to wikipedia L=0..100 u,v=+/-100 but I'm sticking with float
    maybeMagenta = vsgTRIVIAL(0.4,0.4,0.4)
    vsg.vsgSetDrawPage(0)
    vsg.vsgPaletteSet(1, maybeMagenta)
    vsg.vsgSetPen1(1)
    vsg.vsgDrawRect(0,0,vsg.height/2, vsg.height/2)
    vsg.vsgSetDisplayPage(0)

    maybeMagenta.a = 0.8    # Brighter?
    vsg.vsgPaletteSet(2, maybeMagenta)
    vsg.vsgSetPen1(2)
    vsg.vsgDrawRect(0,0,vsg.height/1.5, vsg.height/4)
    

    
    
        
    

