#!/usr/bin/env python

"""

An attempt to interface directly to the Visage VSG DLL library and wrap
it up in a python class. This is so I can attempt to get the sameDiffColorsHSL
experiment working with minimum hackage

The DLL thunking is all handled by the ctypes package

"""

import sys
from ctypes import *

vsgVIDEOPAGE=256;

class vsgTRIVIAL(Structure):
    _fields_ = [ ("red", c_double),
                 ("green", c_double),
                 ("blue", c_double) ]
    
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
    vsg = PyVSG()
    red = vsgTRIVIAL(1.0, 0, 0)
    vsg.vsgPaletteSet(1, red)
    vsg.vsgSetPen1(1)
    vsg.vsgDrawRect(0,0,vsg.height/2, vsg.height/2)

    size = vsg.height/2
    index = 1;
    while index<255:
        index = index + 1
        red.red = red.red*0.95
        size = size * 0.95
        vsg.vsgPaletteSet(index, red)
        vsg.vsgSetPen1(index)
        vsg.vsgDrawRect(0,0,size,size)

    """ Finally ensure we display the page we have been drawing on """
    
        
    

