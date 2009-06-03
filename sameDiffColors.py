#!/usr/bin/env python
#
# sameDiffColours
#
# A psychological colour perception experiment.
#
# (C) 2009 Gary Lupyan - original test
# (C) 2009 Alex Bennee <alex@bennee.com> - refactoring and VISAGE hacks
#
# This program is licensed under the GPLv3. The VisionEgg and Quest algorithm have their
# own license restrictions. Please see those files for details.
#

"""To Do:
Limit exposure and mask the color swatches?
Have invalid label cues?

"""

############################
#  Import various modules  #
############################

import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()

from VisionEgg.Core import *
from VisionEgg.FlowControl import Presentation, FunctionController
from VisionEgg.MoreStimuli import *
from VisionEgg.Text import *
from VisionEgg.FlowControl import Presentation
from VisionEgg.Textures import *
from math import *
import pygame
from pygame.locals import *
from VisionEgg.WrappedText import *
import optparse
from optparse import OptionParser
import glob
import os
import sys
import random
from math import *
import numpy as num

#
# Bring in the PyVSG library which will be duplicating what we see on the main screen
# on the Visage display. As it's in this work directory we need to set PYTHONPATH which
# influences where import will look for modules.
#

#set path to current directory
path = os.getcwd() 
print 'path is ' + str(path)
os.environ["PYTHONPATH"]=path
sys.path.append(path)

import Quest
import PyVSG

############################
# Globals                  #
############################

# VISAGE library bindings
vsg = PyVSG.PyVSG()

# list of Colours used in the trial
listOfColours = []
# list of Trials
listOfTrials = []

#
# The reset of the control flow is at the bottom of this file, what follows is defining the classes
# we will need to run the experiment
#

#
# Define a class to contain a colour for the experiment
# This allows us to absract some of the repeated logic for RGB into
# this class making the logic easier to follow
#
class Colour:

        # String representation of colour
        def __str__(self):

                rgb_str = "rgb: %f, %f, %f" % (self.RGB.a, self.RGB.b, self.RGB.c)
                cie_str = "cie: %f, %f, %f" % (self.CIE.a, self.CIE.b, self.CIE.c)
                
                if self.target:
                        st = "Target Colour: %s (%s/%s)" % (self.name,
                                                             rgb_str,
                                                             cie_str)
                else:
                        st = "Quest Colour: %s (%s/%s)" % (self.name,
                                                            rgb_str,
                                                            cie_str)
                        
                return st

        # class contructor
        def __init__(self, name, colRGB, offset=0.15, delta=0.02, sound="", target=True):
                self.name = name

                # Set the colours up
                self.RGB = PyVSG.vsgTRIVIAL(colRGB[0], colRGB[1], colRGB[2])
                self.CIE = vsg.vsgSpaceToSpace(PyVSG.vsgCS_RGB, self.RGB, PyVSG.vsgCS_CIE1976)

                if sound:
                        sound_path = path + "\\" + sound
                        # print "sound_path = %s" % (sound_path)
                        self.sound = pygame.mixer.Sound (sound_path)

                # Only target colours track their quest values
                self.target = target
                if target:
                        print "offset is %f" % offset
                        # For this experiment we vary CIE.a (i.e L*)
                        var = self.CIE.a + offset
                        self.delta = float(delta)
                        self.quest = Quest.QuestObject(  var, # tGuess
                                                         0.2, # tGuessSd (sd of Gaussian)
                                                         0.7, # pThreshold
                                                         3.5, # beta
                                                         0.01, # delta
                                                         0.5,  # gamma
                                                         0.05  # grain
                                                         )
                        print "Created %s" % (self.__str__())
                        
                
        # Update the Quest Object, response is a True/False bool
        # where True indicates the response was correct.
        #
        # I'm fairly sure you should update the Quest object with the current intensity
        # but the original code varied tTest before updating it.
        def updateQuest(self, qColour, response):
                tOld = self.quest.quantile()
                # Get the value we where changing
                value = qColour.CIE.a
                self.quest.update(value, response)
                tNew = self.quest.quantile()

                # tOld and qColour will vary
                print "Colour::updateQuest %s/%s => %s" % (tOld, value, tNew)

                # update the quest object


        # used for getQuestColour as we actually work in CIE
        def setColourCIE(self, a, b, c):
                self.CIE = PyVSG.vsgTRIVIAL(a, b, c)
                self.RGB = vsg.vsgSpaceToSpace(PyVSG.vsgCS_CIE1976, self.CIE, PyVSG.vsgCS_RGB)
        
        #
        # Abstraction of colour arrays.
        #
        # As we could be working with many different colour schemes the following
        # two functions return a triple value in whatever colour scheme seems
        # appropriate. This means all the messing about with which variable to change
        # and what colour scheme to use can be hidden in here.
        #
        
        # This will be the target colour with a quest variation
        def getQuestColour(self):
                # We create a new colour object and then manually set the CIE colour
                # (the RGB will be updated via VISAGE's colour space conversion)
                fakeRGB = (0.0, 0.0, 0.0)
                questCol = Colour(self.name, (fakeRGB), target=False)

                # Set colours to a + diff, b + diff, c
                tDiff = random.choice( [-self.delta, 0.0, self.delta])
                tNewA = self.quest.quantile() + tDiff
                tNewB = self.CIE.b + tDiff
                questCol.setColourCIE(tNewA, tNewB, self.CIE.c)
                return questCol

        # As VisionEgg wants these we create a list
        def asRGB(self):
                rgb = ( self.RGB.a, self.RGB.b, self.RGB.c )
                return rgb

        # As VISAGE deals with CIE we pass back the normal object
        def asCIE(self):
                return self.CIE

        # Makes the result handling neater
        def asCIEstr(self):
                val = "%f,%f,%f" % (self.CIE.a, self.CIE.b, self.CIE.c)
                return val
                

        #
        # calculateColourDistance
        #
        # To abstract it awy from the experiment so it can be tweaked for different
        # colour spaces.
        #
        def calculateColourDistance(self, questColour):
                distanceA = self.CIE.a - questColour.CIE.a
                distanceB = self.CIE.b - questColour.CIE.b
                st = "%f/%f" % (distanceA, distanceB)
                return st
        
        
# Define class to wrap up an individual trial           
class Trial:

        # Generate a printable reprentation of this trial
        def __str__(self):
                st = "Trial: %s" % (self.colour.name)
                return st
        
        def __init__(self, colour):
                self.colour = colour
                print "Created %s" % (self.__str__())
        
class Exp:
        def __init__(self):
        
                #this is where the subject variables go.  'any' means any value is allowed as long as it's the correct type (str, int, etc.) the numbers 1 and 2 control the order in which the prompts are displayed (dicts have no natural order)
                self.allSubjVariables = {'1':  {'name' : 'subjCode', 
                                                'prompt' : 'Enter Subject Code: ', 
                                                'options': ('any'), 
                                                'type' : str}, 
                                         '2' : {'name' : 'gender', 
                                                'prompt' : 'Enter Subject Gender M/F: ', 
                                                'options' : ("M","F"), 
                                                'type' : str}}

                print "Getting subject variables"
                self.getSubjVariables()
                print "get_default_screen"

                # Start up with default VisionEgg screen
                #
                # As this version of the experiment is duplicating information on the VISAGE
                # system we want to disable the GUI prompt and use what we know about the PyVSG class
                # for the creation of the OpenGL screen
                VisionEgg.config.VISIONEGG_GUI_INIT = 0
                VisionEgg.config.VISIONEGG_SCREEN_W = vsg.width
                VisionEgg.config.VISIONEGG_SCREEN_H = vsg.height
                self.screen = get_default_screen()
                self.screen.parameters.bgcolor = (0.0,0.0,0.0,1.0)

                # Set VISAGE to CIE colour space
                vsg.vsgSetColourSpace(PyVSG.vsgCS_CIE1976)
                vsg.vsgSetDrawPage(0)

		# Set 0,0 as bottom left
		vsg.vsgSetDrawOrigin(0,vsg.height)
                
                self.preFixationDelay  =        0.250
                self.postFixationDelay  =       0.500
		
                self.numBlocks = 30
                self.takeBreakEveryXTrials = 5
		
                self.finalText = "You've come to the end of the experiment.  Thank you for participating."
                self.instructions = \
		"""In this experiment you will see four colors arranged in a square.\n """ \
		"""One of those colors will be different from the others.\n  """\
		"""Your task is to decide which color is different. Before each trial,\n """\
		"""you will hear a voice ask which of the colors or which of reds/blues/greens is different\n."""\
		"""  Your task is exactly the same regardless of whether you hear a color name or the word "color"\n\n\n"""
		self.instructions = \
		    self.instructions + """Use the number keys on the number pad for responding in the direction of the different color:\n
							7 | 8\n
							--|--\n
							4 | 5\n
		"""		

                self.thanks = "Thank you for participating \n Please let the experimenter know if you have any questions."
                self.takeBreak = "Please take a short break.\n  Press any button when you are ready to conitnue"
                self.practiceTrials = "The next part is practice"
                self.realTrials = "Now for the real trials"
                
                if  os.path.isfile(self.subjVariables['subjCode']+'.txt'):
                        sys.exit('output file exists, try a different subject code')
                else:
                        self.outputFile = file(self.subjVariables['subjCode']+'.txt','w')

                print "End of Exp:__init__"
                print self.subjVariables

        def getSubjVariables(self):
                def checkInput(value,options,type):
                        """Checks input.  Uses 'any' as an option to check for any <str> or <int>"""
                        try:
                                #if the user typed something and it's an instance of the correct type and it's in the options list...
                                if value and isinstance(value,type) and ('any' in options or value.upper() in options ):
                                        return True
                                return False
                        except:
                                print"Try again..."
                self.subjVariables = {}
                for curNum, varInfo in sorted(self.allSubjVariables.items()):
                        curValue=''
                        while not checkInput(curValue,varInfo['options'],varInfo['type']):
                                curValue = raw_input(varInfo['prompt'])
                        if not 'any' in varInfo['options']:
                                curValue = str(curValue.upper())
                        self.subjVariables[varInfo['name']] = curValue
                
        def writeToFile(self,trial):
                """Writes a trial (array of lists) to a fileHandle"""
                line = '\t'.join([str(i) for i in trial]) #TABify
                line += '\n' #add a newline
                #print "writeToFile:" + str(line)
                self.outputFile.write(line)
                self.outputFile.flush() # write to disk now!

        # Store our results
        def storeResults(self, results):
                # First add the subject info
                results.insert(0,self.subjVariables["gender"])
                results.insert(0,self.subjVariables["subjCode"])
                #print "results:" + str(results)
                self.writeToFile(results)

	# Convert from presentation co-ordinates (0,0 center, +x right, +y up)
	#           to VisionEgg co-ordinates (0,0 bottom left, +x right, +y up)
        def convertFromPresentationToVECoordinates(self,(xy),width=0):
                x=xy[0]
                y=xy[1]
		# print "convertFromPresentationToVECoordinates: (%d x %d), width=%d" % (x, y, width)
                nx=x + self.screen.size[0]/2 - width/2
                ny=y + self.screen.size[1]/2
		
                # print "  = (%d x %d)" % (nx, ny)
                return (nx,ny)

                        
	# Convert from VisionEgg co-ordinates (0,0 bottom left, +x right, +y up)
	#           to VISAGE co-ordinates (0,0 bottom left, +x right, -y up)
	def convertFromVEtoVSGCoordinates(self, (xy)):
		x = xy[0]
		y = xy[1]
		# print "convertFromVEtoVSGCoordinates: (%d x %d)" % (x, y)
		nx = x
		ny = -y
		
		# print "  = (%d x %d)" % (nx, ny)
		return (nx,ny)
		


                       
class ExpPresentation:
        """Functions related to presenting stimuli"""
        def __init__(self,experiment):
                print "ExpPresentation:__init__"
                self.experiment = experiment


                self.fix1 = Target2D(
                        anchor = 'center',
                        color = (1,1,1),
                        on = 1,
                        orientation = 0,
                        position = self.experiment.convertFromPresentationToVECoordinates((0,0)),
                        size = (2,15)
                        )

                self.fix2 = Target2D(
                        anchor = 'center',
                        color = (1,1,1),
                        on = 1,orientation = 0,
                        position = self.experiment.convertFromPresentationToVECoordinates((0,0)),
                        size = (15,2)
                        )


                self.text = Text(
                        anchor = 'center',
                        text = 'testing',
                        color = (1,1,1),
                        position = self.experiment.convertFromPresentationToVECoordinates((0,0))
                        )

		boxSize = 100
		
                # top left box
                self.firstStim  = Target2D(
                        anchor = 'center',
                        color = (1,0,0),
                        on = 1,
                        orientation = 0,
                        position = self.experiment.convertFromPresentationToVECoordinates((-125,125)),
                        size = (boxSize,boxSize)
                        )

                # top right box
                self.secondStim  = Target2D(
                        anchor = 'center',
                        color = (0,1,0),
                        on = 1,
                        orientation = 0,
                        position = self.experiment.convertFromPresentationToVECoordinates((125,125)),
                        size = (boxSize,boxSize)
                        )


		# bottom left box
                self.thirdStim  = Target2D(
                        anchor = 'center',
                        color = (0,0,1),
                        on = 1,
                        orientation = 0,
                        position = self.experiment.convertFromPresentationToVECoordinates((-125,-125)),
                        size = (boxSize,boxSize)
                        )

                # bottom right box
                self.forthStim  = Target2D(
                        anchor = 'center',
                        color = (1,1,1),
                        on = 1,
                        orientation = 0,
                        position = self.experiment.convertFromPresentationToVECoordinates((125,-125)),
                        size = (boxSize,boxSize)
                        )

                                                
                self.viewport_fixation  = Viewport( screen = self.experiment.screen, stimuli=[self.fix1,self.fix2] ) #fixation cross
                self.viewport_trial     = Viewport( screen = self.experiment.screen) #set dynamically below
                
                
        def convertFromRGB(self,decimalTriplet):
                return decimalTriplet/255.0
                
        
        def showWrappedText(self,message,position=(0,300),width=800):
                if position=="center":
                        position = (-100,0)
                        width=0

		vePos = self.experiment.convertFromPresentationToVECoordinates(position,width)
                wt = WrappedText(text=message, 
                                 position=vePos,
                                 size=(800, 600),
                                 color=(1,1,1))
                self.viewport_trial.parameters.stimuli = [wt]

		# Draw on VISAGE - this breaks
		vsgPos = self.experiment.convertFromVEtoVSGCoordinates(vePos)
                vsg.vsgSetDrawPage(0)
		vsg.vsgDrawString(vsgPos[0], vsgPos[1], message)
		vsg.vsgSetDisplayPage(0)
		
                while pygame.event.wait().type != KEYDOWN:
                        self.presentStimulus(self.viewport_trial)
                
        def showText(self,textToShow):
                self.text.parameters.text = textToShow
                self.viewport_trial.parameters.stimuli = [self.text]

		# Draw on VISAGE
		vePos = self.experiment.convertFromPresentationToVECoordinates((0,0))	
		vsgPos = self.experiment.convertFromVEtoVSGCoordinates(vePos)
                vsg.vsgSetDrawPage(0)
		vsg.vsgDrawString(vsgPos[0], vsgPos[1], textToShow)
		vsg.vsgSetDisplayPage(0)

                while pygame.event.wait().type != KEYDOWN:
                        self.presentStimulus(self.viewport_trial)

			

        # Parse a line of experiment control file
        # to define a colour and it's associated sound
        def defineColourFromLine(self, line):
                array = line.split(None) # whitespace
                # print "define colour: %s" % array
                cols = array[2].split(",")
                rgb = []
                for c in cols:
                        rgb.append(float(c))
                colour = Colour(array[1],
                                rgb,
                                float(array[3]),
                                float(array[4]),
                                array[5])
                listOfColours.append(colour)
		trial = Trial(colour)
                listOfTrials.append(trial)

        def readTrials(self,fileName):
                """This reads the trials from a specified file"""
                f = file(fileName, "r")
                line = f.readline()
                while line:
                        # drop the newline
                        line.strip()
                        if line[0] == "#":
                                # ignore comments
                                # print "Skipping comment line: %s" % line
                                pass
                        elif line.find("define")==0:
                                # define a colour
                                self.defineColourFromLine(line)
			# next line
                        line = f.readline()
                

        def presentStimulus(self,display):
                self.experiment.screen.clear()
                display.draw()
                swap_buffers()

        def setAndPresentStimulus(self,stimuli):
                self.experiment.screen.clear()
                self.viewport_trial.parameters.stimuli = stimuli
                self.viewport_trial.draw()
                swap_buffers()

                
        def initializeExperiment(self):
                """This loads all the stimili into proper lists and initializes the trial sequence"""
                loadWhichFile = 'trialListColors.txt'
                self.trialListMatrix = self.readTrials(loadWhichFile)
        
        
        def checkExit(self,event):
                if event.key == pygame.locals.K_ESCAPE:
                        print "experiment terminated by user"
                        sys.exit()
        
        #
        # presentExperimentTrial
        #
        # Run a single experiment and gather the subjects response. Returns
        # an isRight/isWrong response for the next iterations calculations
        #
   
        def presentExperimentTrial(self,curBlock,trial,whichPart,expNo, targetColour, questColour):

                #
                # Play the sound cue. 
                #
                def playAudioCue(self):

                        # Play a sound until pygame has finished it
                        def playAndWait(sound):
                                sound.play()
                                while pygame.mixer.get_busy():
                                        clock.tick(30)

                        # Play the intro
                        clock = pygame.time.Clock()
                        # And the colour sound
                        playAndWait(trial.colour.sound)

		#
		# Draw a VisionEgg Rect using the VISAGE drawing functions
		#
		# This takes a VE Target2D rect stim and draws it with VISAGE.
		# It will very likey get confused if things if the stim is not a simple
		# normally oriantated rectangle.
		#
		# Note: Colours will have gone RGB->CIE->RGB->CIE by the end of this
		#       I don't think we are in the bounds of having to worry about
		#       floating point issues, I think.
		#
		def drawVisionEggRectWithVSG(stim):
			# Colour from stim defintion, convert to CIE
			stim_cols = stim.parameters.color
			rgb = PyVSG.vsgTRIVIAL(stim_cols[0], stim_cols[1], stim_cols[2])
			cie = vsg.vsgSpaceToSpace(PyVSG.vsgCS_RGB, rgb, PyVSG.vsgCS_CIE1976)
			vsg.vsgSetDrawColour(cie)
			
			pos = self.experiment.convertFromVEtoVSGCoordinates(stim.parameters.position)
			size = stim.parameters.size
			vsg.vsgDrawRect(pos[0], pos[1], size[0], size[1])
			
		

		# Decide which of our 4 blocks is the odd one out (top left, top right, bottom left, bottom right)
		oddOne = random.randint(1,4);
                print "presentExperimentTrial: oddOne=%d" % (oddOne)
		print "  target is %s" % (targetColour)
		print "  quest is %s" % (questColour)

		# DEBUG, uncomment if you want to check which one
		# really is the odd one out
		# questColour.setColourCIE(20, 20, 20)

		# Set the colours of the stimuli
		self.firstStim.parameters.color  = (list(questColour.asRGB()) if oddOne == 1 else list(targetColour.asRGB()))
		self.secondStim.parameters.color = (list(questColour.asRGB()) if oddOne == 2 else list(targetColour.asRGB()))
		self.thirdStim.parameters.color  = (list(questColour.asRGB()) if oddOne == 3 else list(targetColour.asRGB()))
		self.forthStim.parameters.color  = (list(questColour.asRGB()) if oddOne == 4 else list(targetColour.asRGB()))
		
                # First clear screen and wait for some specified time
                
                # VE:
                self.setAndPresentStimulus([])
                # VISAGE
                vsg.vsgSetDrawPage(0)
                vsg.vsgSetDisplayPage(1)

                time.sleep(self.experiment.preFixationDelay)

		# Show fixation cross
		
                # VE:
                self.presentStimulus(self.viewport_fixation)
                # VISAGE:
		drawVisionEggRectWithVSG(self.fix1)
		drawVisionEggRectWithVSG(self.fix2)
                vsg.vsgSetDisplayPage(0)
                
                # Play the audio cue and wait
                playAudioCue(self)
                time.sleep(self.experiment.postFixationDelay)

		# fixation + 4 boxes
                # VE:
                self.setAndPresentStimulus([self.fix1,
					    self.fix2,
					    self.firstStim,
					    self.secondStim,
					    self.thirdStim,
					    self.forthStim])
                # VISAGE
                vsg.vsgSetDrawPage(1)
		drawVisionEggRectWithVSG(self.fix1)
		drawVisionEggRectWithVSG(self.fix2)

		# Draw the 4 VISAGE boxes
		drawVisionEggRectWithVSG(self.firstStim)
		drawVisionEggRectWithVSG(self.secondStim)
		drawVisionEggRectWithVSG(self.thirdStim)
		drawVisionEggRectWithVSG(self.forthStim)

                # switch to display 1
                vsg.vsgSetDisplayPage(1)
                
                responded = False
                timeElapsed = False
                pygame.event.clear() #discount any keypresses
                responseStart = time.time()
                while not responded: 
                        # VE: self.setAndPresentStimulus([self.fix1, self.fix2,self.firstStim, self.secondStim]) #fixation + first pic + second pic
                        for event in pygame.event.get(pygame.KEYDOWN):
                                if event.key == pygame.locals.K_KP7 or event.key == pygame.locals.K_KP9 or event.key == pygame.locals.K_KP1 or event.key == pygame.locals.K_KP3:
                                        response = event.key
					if event.key == pygame.locals.K_KP7:
						responsePos = 1
					elif event.key == pygame.locals.K_KP9:
						responsePos = 2
					elif event.key == pygame.locals.K_KP1:
						responsePos = 3
					elif event.key == pygame.locals.K_KP3:
						responsePos = 4
                                        rt = time.time() - responseStart
                                        pygame.event.clear()
                                        responded = True
                                        break

                # Was the response correct
		if oddOne == responsePos:
			isRight = True
		else:
			isRight = False
			
                dist = targetColour.calculateColourDistance(questColour)

                
                print "presentExperimentTrial: correct:%s time:%f dist:%s" % (isRight, rt, dist)

                # Dump run to results file.
                results = []
                results.append(expNo)
                results.append(targetColour.name)
                results.append(isRight)
		results.append(oddOne)
                results.append(targetColour.asCIEstr())
                results.append(questColour.asCIEstr())
                results.append(dist)
                results.append(rt)
                self.experiment.storeResults(results)
                
                
                return isRight


        
        def getPsychometricFunctions(self,whichPart):

                print "getPsychometricFunctions"
		numTrials = len(listOfTrials)
		numBlocks = self.experiment.numBlocks

                totalExperiments = 0
                
                print "Starting sequence: blocks=%d, trials per block=%d" % (numBlocks, numTrials)
                
                for curBlock in range(numBlocks):
                        # Shuffle the trial list for each block of tests
                        random.shuffle(listOfTrials)
                        
                        for trial in listOfTrials:

                                #
                                # Ensure we take breaks
                                #
                                totalExperiments = totalExperiments + 1
                                if totalExperiments % self.experiment.takeBreakEveryXTrials == 0:
                                        self.showText(self.experiment.takeBreak)

                                print "Doing %s" % trial

                                # Time to get the colours
                                targetColour = trial.colour
                                questColour = targetColour.getQuestColour()

                                """This is what's shown on every trial"""
                                response = self.presentExperimentTrial(curBlock,trial,whichPart, totalExperiments, targetColour, questColour)
				trial.colour.updateQuest(questColour, response)

                                print "Done Trial\n"

"""
This is the start of the Experiment
"""

print "Start of Experiment"

#initialize sound system
pygame.mixer.init()

# Set up the experiment
currentExp = Exp()
currentPresentation = ExpPresentation(currentExp)
currentPresentation.initializeExperiment()

# Show the instrcution text and wait for a button press
pygame.event.clear() #clear any residual button presses
currentPresentation.showWrappedText(currentExp.instructions) #show the instructions

# Run the experiment
#
# Passing "practice" forces a single itteration for the sake of testing
currentPresentation.getPsychometricFunctions("questNothingVsColor")
#currentPresentation.getPsychometricFunctions("practice")

# Thank the subject
currentPresentation.showWrappedText(currentExp.thanks)
