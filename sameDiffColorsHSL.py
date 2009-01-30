#!/usr/bin/env python

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
import random
from math import *
import numpy as num
import Quest

#
# Bring in the PyVSG library which will be duplicating what we see on the main screen
# on the Visage display. As it's in this work directory we need to set PYTHONPATH which
# influences where import will look for modules.
#

#set path to current directory
path = os.getcwd() 
print 'path is ' + str(path)
os.environ["PYTHONPATH"]=path

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
	def __init__(self, name, colRGB, sound):
		self.name = name
		self.sound = sound
		self.RGB = colRGB
		

	def getName(self):
		return self.name
	

# Define class to wrap up an individual trial		
class Trial:
	def __init__(self, colour, labeled, sameDiff):
		self.colour = colour

		if sameDiff == "same":
			self.same = True
		else:
			self.same = False

		self.labeled = labeled

		if self.same == True:
                        sameStr = "same"
                else:
                        sameStr = "diff"

                if self.labeled == True:
                        labelStr = "labelled"
                else:
                        labelStr = "unlabelled"
                        
		print "Created Trail object: Colour:%s, %s, %s" % (colour.getName(), sameStr, labelStr)
	
	
#class trial(Exp): 
#        def __init__(self):
#                colorCategory=''
#                isLabel=''
#                sameDiff=''


class Exp:
        def __init__(self):
        
                #this is where the subject variables go.  'any' means any value is allowed as long as it's the correct type (str, int, etc.) the numbers 1 and 2 control the order in which the prompts are displayed (dicts have no natural order)
                self.allSubjVariables = {'1':  {'name' : 'subjCode', 
						'prompt' : 'Enter Subject Code: ', 
						'options': ('any'), 
						'type' : str}, 
					 '2' : {'name' : 'whichSame', 
						'prompt' : 'Which Key for Same: z or /: ', 
						'options' : ("Z","/"), 
						'type' : str},
					 '3' : {'name' : 'gender', 
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

                
                self.preFixationDelay  =        0.250
                self.postFixationDelay  =       0.500
                if self.subjVariables['whichSame'] == "Z":
                        self.sameResp = pygame.locals.K_z
                        self.diffResp = pygame.locals.K_SLASH
                        responseText = "Press the 'z' key for 'Yes' (the two colors are exactly the same) and the '/' key for 'No' (the two colors are slightly different)"
                else:
                        self.sameResp = pygame.locals.K_SLASH
                        self.diffResp = pygame.locals.K_z
                        responseText = "Press the '/' key for 'Yes' (the two colors are exactly the same) and the 'z' key for 'No' (the two colors are slightly different)"
                

                self.stimPositions = {}
                self.stimPositions['left'] = self.convertFromPresentationStyleCoordinates((-75,0))
                self.stimPositions['right'] = self.convertFromPresentationStyleCoordinates((75,0))
                
                self.numBlocks = 10
                self.numPracticeTrials = 5
                self.numStaircaseTrials = 120
                self.takeBreakEveryXTrials = 200 
                self.finalText              = "You've come to the end of the experiment.  Thank you for participating."
                self.instructions               = \
                """In this experiment you will see pairs of colors.  Sometimes the colors will be identical.  Other times they will be very slightly different shades of red.  Before each trial, you will hear a voice ask if the two colors or the two reds are the same.  If they are *exactly* the same, respond 'yes'.  If they are at all different, respond 'no'.  Whether you hear 'red' or 'colors' doesn't matter because all the colors you see will be shades of red.\n\n\n"""
                self.instructions = self.instructions + responseText

                self.thanks             = \
                "Thank you for participating \n Please let the experimenter know if you have any questions. \
                "
                self.takeBreak = "Please take a short break.\n  Press any button when you are ready to conitnue"
                self.practiceTrials = "The next part is practice"
                self.realTrials = "Now for the real trials"
                
                if  os.path.isfile(self.subjVariables['subjCode']+'.txt'):
                        sys.exit('output file exists, try a different subject code')
                else:
                        self.outputFile = file(self.subjVariables['subjCode']+'.txt','w')

                print "End of Exp:__init__"
                #print self.subjVariables

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
                
        def setupSubjectVariables(self):
                parser = OptionParser()
                parser.add_option("-s", "--subject-id", dest="subjid", help="specify the subject id")

                (options, args)         = parser.parse_args()
                self.subjID             = options.subjid

                if not self.subjID:
                        print "You must provide a Subject ID and design_file"
                        parser.print_help()
                        sys.exit()
        
                
        def writeToFile(self,fileHandle,trial):
                """Writes a trial (array of lists) to a fileHandle"""
                line = '\t'.join([str(i) for i in trial]) #TABify
                line += '\n' #add a newline
                fileHandle.write(line)

        def convertFromPresentationStyleCoordinates(self,(xy),width=0):
                x=xy[0]
                y=xy[1]
                print "convertFromPresentationStyleCoordinates %d x %d" % (x, y)

                # Vision Egg version
                nx=x + self.screen.size[0]/2 - width/2
                ny=y + self.screen.size[1]/2

                # VISAGE version
                #nx=x + vsg.width/2 - width/2
                #ny=y + vsg.height/2

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
			position = self.experiment.convertFromPresentationStyleCoordinates((0,0)),
			size = (2,15)
			)

                self.fix2 = Target2D(
			anchor = 'center',
			color = (1,1,1),
			on = 1,orientation = 0,
			position = self.experiment.convertFromPresentationStyleCoordinates((0,0)),
			size = (15,2)
			)


                self.text = Text(
			anchor = 'center',
			text = 'testing',
			color = (1,1,1),
			position = self.experiment.convertFromPresentationStyleCoordinates((0,0))
			)

                self.firstStim  = Target2D(
			anchor = 'center',
			color = (1,1,1),
			on = 1,
			orientation = 0,
			position = self.experiment.convertFromPresentationStyleCoordinates((-125,0)),
			size = (100,100)
			)

                self.secondStim  = Target2D(
			anchor = 'center',
			color = (1,1,1),
			on = 1,
			orientation = 0,
			position = self.experiment.convertFromPresentationStyleCoordinates((125,0)),
			size = (100,100)
			)

                # Define all the sounds
                self.wrongSound =       pygame.mixer.Sound(path + "\\stimuli\\" + "Buzz3.wav")
                self.correctSound =     pygame.mixer.Sound(path + "\\stimuli\\" + "Bleep3.wav")
                self.carrierSound =     pygame.mixer.Sound(path + "\\stimuli\\" + "areTheTwo.wav")
                self.redSound =         pygame.mixer.Sound(path + "\\stimuli\\" + "reds.wav")
                self.greenSound =       pygame.mixer.Sound(path + "\\stimuli\\" + "greens.wav")
                self.blueSound =        pygame.mixer.Sound(path + "\\stimuli\\" + "blues.wav")
                self.colorSound =       pygame.mixer.Sound(path + "\\stimuli\\" + "colors.wav")
                self.sameSound =        pygame.mixer.Sound(path + "\\stimuli\\" + "same.wav")
                self.diffSound =        pygame.mixer.Sound(path + "\\stimuli\\" + "diff.wav")
                                                
                                                
                self.viewport_fixation  = Viewport( screen = self.experiment.screen, stimuli=[self.fix1,self.fix2] ) #fixation cross
                self.viewport_trial     = Viewport( screen = self.experiment.screen) #set dynamically below

                
        def setUpQuest(self):
                tGuess = -1.0
                tGuessSd = 0.3 # sd of Gaussian before clipping to specified range
                pThreshold = 0.7
                beta = 3.5
                delta = 0.01
                gamma = 0.5
                return Quest.QuestObject(tGuess,tGuessSd,pThreshold,beta,delta,gamma,grain=.03)
                
        def stepQuest(self,q,response):
                tTest=q.quantile()
                #tTest=q.mean()
                #tTest=q.mode()
                tTest=tTest+random.choice([-.02,0,.02])
                q.update(tTest,response);
                return tTest            
                
        def convertFromRGB(self,decimalTriplet):
                return decimalTriplet/255.0
                
        
        def showWrappedText(self,message,position=(0,300),width=800):
                if position=="center":
                        position = (-100,0)
                        width=0
                wt = WrappedText(text=message, 
				 position=self.experiment.convertFromPresentationStyleCoordinates(position,width),
				 size=(800, 600),
				 color=(1,1,1))
                self.viewport_trial.parameters.stimuli = [wt]
                while pygame.event.wait().type != KEYDOWN:
                        self.presentStimulus(self.viewport_trial)
                
        def showText(self,textToShow):
                self.text.parameters.text = textToShow
                self.viewport_trial.parameters.stimuli = [self.text]
                while pygame.event.wait().type != KEYDOWN:
                        self.presentStimulus(self.viewport_trial)

	# Parse a line of experiment control file
	# to define a colour and it's associated sound
	def defineColourFromLine(self, line):
		print "define colour: %s" % line
		array = line.split("\t")
		colour = Colour(array[1],
				(array[2]),
				array[3])
		listOfColours.append(colour)

	# Parse a line of the experiment control file
	# to define an individual test block
	def defineTrialFromLine(self, line):
		print "trial: %s" % line
		array = line.split("\t")
		for colour in listOfColours:
			if colour.name == array[0]:
				trial = Trial(colour, array[1], array[2])
				listOfTrials.append(trial)
				return
		print "Couldn't find colour definition for %s" % array[0]
		exit()
                
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
		        else:
				self.defineTrialFromLine(line)
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
        

        def isResponseCorrect(self,response, firstStim, secondStim):
                if response == self.experiment.sameResp and list(firstStim)==list(secondStim):
                        return 1
                if response == self.experiment.diffResp and list(firstStim) != list(secondStim):
                        return 1
                return 0

                
        #I don't think we need this function for sameDiff...
        def createResponse(self,**respVars):
                trial = [] #initalize array
                #add all the subject variables to the response line
                for curSubjVar, varInfo in sorted(self.experiment.allSubjVariables.items()):
                        trial.append(self.experiment.subjVariables[varInfo['name']])
                trial.append(str(respVars['whichPart']))
                trial.append(str(respVars['curBlock']))
                trial.append(str(respVars['trialIndex']))
                trial.append(str(respVars['colorCategory']))
                trial.append(str(respVars['isLabel']))
                trial.append(str(respVars['sameDiff']))
                trial.append(str(respVars['curDistance']))
                trial.append(str(respVars['firstStim'][0])) #divides up the colors into RGB intensities for printing
                trial.append(str(respVars['firstStim'][1]))
                trial.append(str(respVars['firstStim'][2]))
                trial.append(str(respVars['secondStim'][0]))
                trial.append(str(respVars['secondStim'][1]))
                trial.append(str(respVars['secondStim'][2]))
                trial.append(str(respVars['locationOne']))
                trial.append(str(respVars['locationTwo']))
                trial.append(str(respVars['rt']))
                trial.append(str(respVars['isRight']))
                return trial

        #
        # presentExperimentTrial
        #
        # Run a single experiment and gather the subjects response. Returns
        # an isRight/isWrong response for the next iterations calculations
        #
   
        def presentExperimentTrial(self,curBlock,trialIndex,whichPart,color1,color2):

                #
                # Play the sound cue. 
                #
                def playAudioCue(self):
                        def playAndWait(sound):
                                sound.play()
                                while pygame.mixer.get_busy():
                                        clock.tick(30)                          
                        colorCategory = self.trialListMatrix[trialIndex].colorCategory
                        isLabel = int(self.trialListMatrix[trialIndex].isLabel)
                        colorSoundsDict = {'red': self.redSound, 'green': self.greenSound, 'blue': self.blueSound}

                        clock = pygame.time.Clock()
                        playAndWait(self.carrierSound)
                        
                        if isLabel==1:
                                playAndWait(colorSoundsDict[colorCategory])
                        else:
                                playAndWait(self.colorSound)

                        playAndWait(self.sameSound)

                # start of presentExperimentTrial

                # First clear screen and wait for some specified time
                
                # VE:
                self.setAndPresentStimulus([])
                # VISAGE
                vsg.vsgSetDrawPage(0)
                vsg.vsgSetDisplayPage(1)

                time.sleep(self.experiment.preFixationDelay)

                # VE:
                self.presentStimulus(self.viewport_fixation) #show fixation cross
                # VISAGE:
                white = PyVSG.vsgTRIVIAL(1.0, 1.0, 1.0)
                vsg.vsgPaletteSet(1, white)
                vsg.vsgSetPen1(1)
                vsg.vsgDrawRect(0,0,10,2)
                vsg.vsgDrawRect(0,0,2,10)
                vsg.vsgSetDisplayPage(0)
                
                # Play the audio cue and wait
                playAudioCue(self)
                time.sleep(self.experiment.postFixationDelay)

                # VE:
                self.setAndPresentStimulus([self.fix1, self.fix2,self.firstStim, self.secondStim]) #fixation + first pic + second pic
                # VISAGE
                vsg.vsgSetDrawPage(1)
                # cross
                vsg.vsgPaletteSet(1, white)
                vsg.vsgSetPen1(1)
                vsg.vsgDrawRect(0,0,10,2)
                vsg.vsgDrawRect(0,0,2,10)
                # left box
                leftColour = PyVSG.vsgTRIVIAL(color1[0],color1[1],color1[2])
                vsg.vsgPaletteSet(2, leftColour)
                vsg.vsgSetPen1(2)
                vsg.vsgDrawRect(-125, 0, 100, 100)
                # right box
                rightColour = PyVSG.vsgTRIVIAL(color2[0],color2[1],color2[2])
                vsg.vsgPaletteSet(3, rightColour)
                vsg.vsgSetPen1(3)
                vsg.vsgDrawRect(125, 0, 100, 100)
                # switch to display 1
                vsg.vsgSetDisplayPage(1)
                
                responded = False
                timeElapsed = False
                pygame.event.clear() #d  count any keypresses
                responseStart = time.time()
                while not responded: 
                        # VE: self.setAndPresentStimulus([self.fix1, self.fix2,self.firstStim, self.secondStim]) #fixation + first pic + second pic
                        for event in pygame.event.get(pygame.KEYDOWN):
                                if event.key == self.experiment.sameResp or event.key == self.experiment.diffResp:
                                        response = event.key
                                        rt = time.time() - responseStart
                                        pygame.event.clear()
                                        responded = True
                                        break
                isRight = self.isResponseCorrect(response, color1,color2)
                #play feedback
                #if isRight:
                        #self.correctSound.play()
                #else:
                        #self.wrongSound.play()
                isSame = bool(list(color1)==list(color2))
                print "isRight " + str(isRight) + "rt: " + str(rt)
                curLine = self.createResponse(
			whichPart=whichPart, 
			curBlock=curBlock+1,
			trialIndex=trialIndex+1,
			colorCategory=self.trialListMatrix[trialIndex].colorCategory,
			isLabel = self.trialListMatrix[trialIndex].isLabel,
			sameDiff=self.trialListMatrix[trialIndex].sameDiff,
			curDistance = self.curDistance,
			locationOne = self.locations[0],
			locationTwo = self.locations[1],
			firstStim=color1,
			secondStim=color2,
			rt=rt*1000,
			isRight=isRight) 
                self.writeToFile(self.experiment.outputFile,curLine)
                return bool(isRight)

        def HSL_2_RGB(self,(H,S,L)):
                
                def rounded(float):
                        return int(math.floor(float+0.5))
                                                
                def Hue_2_RGB(v1, v2, vH):
                        if ( vH < 0 ):
                                vH += 1
                        if ( vH > 1 ):
                                vH -= 1
                        if ( ( 6.0 * vH ) < 1.0 ):
                                return ( v1 + ( v2 - v1 ) * 6.0 * vH )
                        if ( ( 2.0 * vH ) < 1.0 ):
                                return v2 
                        if ( ( 3.0 * vH ) < 2.0 ):
                                return ( v1 + ( v2 - v1 ) * ( .666667 - vH ) * 6.0 )
                        return v1 

                if (S == 0 ):
                        R = L * 255
                        G = L * 255
                        B = L * 255
                else:
                        if ( L < 0.5 ):
                                var_2 = L * ( 1 + S )
                        else:
                                var_2 = ( L + S ) - ( S * L )
                        var_1 = 2 * L - var_2
                        R = rounded(255 * Hue_2_RGB( var_1, var_2, H + .333333 ))
                        G = rounded(255 * Hue_2_RGB( var_1, var_2, H ))
                        B = rounded(255 * Hue_2_RGB( var_1, var_2, H - .333333 ))
                return num.array([R,G,B])


        
        def getPsychometricFunctions(self,whichPart):

                def updateColorDistance(self):
                        colorCategory = self.trialListMatrix[trialIndex].colorCategory
                        isLabel = int(self.trialListMatrix[trialIndex].isLabel)
                        if colorCategory=="red":
                                if isLabel:
                                        self.curDistanceRedL = self.stepQuest(self.qRedL,response)
                                else:
                                        self.curDistanceRedNL = self.stepQuest(self.qRedNL,response)
                        elif colorCategory=="green":
                                if isLabel:
                                        self.curDistanceGreenL = self.stepQuest(self.qGreenL,response)
                                else:
                                        self.curDistanceGreenNL = self.stepQuest(self.qGreenNL,response)
                        elif colorCategory=="blue":
                                if isLabel:
                                        self.curDistanceBlueL = self.stepQuest(self.qBlueL,response)
                                else:
                                        self.curDistanceBlueNL = self.stepQuest(self.qBlueNL,response)
                                

                def setBaseColorAndDistance(self):
                        colorCategory = self.trialListMatrix[trialIndex].colorCategory 
                        isLabel = int(self.trialListMatrix[trialIndex].isLabel)
                        print "isLabel is " + str(isLabel)
                        if colorCategory=="red":
                                self.baseColor = self.convertFromRGB(self.HSL_2_RGB(num.array([0.0,1.0,.35]))) #0, 100, 84
                                print "red RGB basecolor is " + str(self.baseColor)
                                if isLabel==1:
                                        self.curDistance = self.curDistanceRedL
                                else:
                                        self.curDistance = self.curDistanceRedNL                                        
                        elif colorCategory=="green":
                                self.baseColor = self.convertFromRGB(self.HSL_2_RGB(num.array([0.308,1.0,.35]))) #111, 100, 84
                                print "green RGB basecolor is " + str(self.baseColor)
                                if isLabel==1:
                                        self.curDistance = self.curDistanceGreenL
                                else:
                                        self.curDistance = self.curDistanceGreenNL
                        elif colorCategory=="blue":
                                self.baseColor = self.convertFromRGB(self.HSL_2_RGB(num.array([0.675,1.0,.35]))) #243, 100, 84
                                print "blue RGB basecolor is " + str(self.baseColor)
                                if isLabel==1:
                                        self.curDistance = self.curDistanceBlueL
                                else:
                                        self.curDistance = self.curDistanceBlueNL

                print "getPsychometricFunctions"
                self.locations = ["left","right"]


                #set up Quest objects (staircases)
                self.qRedL = self.setUpQuest()
                self.qRedNL = self.setUpQuest()
                self.qGreenL = self.setUpQuest()
                self.qGreenNL = self.setUpQuest()
                self.qBlueL = self.setUpQuest()
                self.qBlueNL = self.setUpQuest()
                
                #set initial distances (Quest intensities)
                self.curDistanceRedL =          self.qRedL.tGuess
                self.curDistanceRedNL =         self.qRedNL.tGuess
                self.curDistanceGreenL =        self.qGreenL.tGuess
                self.curDistanceGreenNL =       self.qGreenNL.tGuess
                self.curDistanceBlueL =         self.qBlueL.tGuess
                self.curDistanceBlueNL =        self.qBlueNL.tGuess

                if whichPart == "practice":
                        print "doing practice run"
                        numTrials = self.experiment.numPracticeTrials
                        numBlocks = 1
                else:
                        numTrials = len(self.trialListMatrix)
                        numBlocks = self.experiment.numBlocks

                print "Starting sequence: blocks=%d, trials per block=%d" % (numBlocks, numTrials)
                
                for curBlock in range(numBlocks):                       
                        random.shuffle(self.trialListMatrix) #shuffle the trial list (once per block)
                        for trialIndex in range(numTrials):                     
                                #take break every X trials (for blocks that have hundreds of trials....)
                                if trialIndex>0 and trialIndex % self.experiment.takeBreakEveryXTrials == 0:
                                        self.showText(self.experiment.takeBreak) #take a break

                                random.shuffle(self.locations) #shuffle the locations - every trial
                                
                                
                                setBaseColorAndDistance(self) #sets the base color and distance.  self.curDistance now points to redL, redNL, greenL, etc.... as appropriate for the current trial.
                                firstColorHue =         self.baseColor[0]+abs(1-1/(1+10**self.curDistance))/2.0
                                secondColorHue =        self.baseColor[0]-abs(1-1/(1+10**self.curDistance))/2.0

                                #self.convertFromRGB(self.HSL_2_RGB(num.array([firstColorHue,1.0,.35])))
                                firstColor = (firstColorHue,self.baseColor[1],self.baseColor[2])
                                secondColor = (secondColorHue,self.baseColor[1],self.baseColor[2])
                                        
                                
                                #if this is a "same" (catch) trial.. set the two colors to be the same
                                if self.trialListMatrix[trialIndex].sameDiff=="same":
                                        if random.random>.5:
                                                firstColor=secondColor
                                        else:
                                                secondColor=firstColor

                                print "baseColor is " + str(self.baseColor) + "\n"
                                print "baseColor hue " + str(self.baseColor[0]) + "\n"
                                print "firstColorHue is " + str(firstColorHue) + "\n"
                                print "firstColor is " + str(firstColor) + "\n"
                                print "secondColorHue is " + str(secondColorHue) + "\n"
                                print "secondColor is " + str(secondColor) + "\n"

                                                
                                #set the colors
                                self.firstStim.parameters.color = list(firstColor)
                                self.secondStim.parameters.color = list(secondColor)
                                
                                #set the screen locations of the stimuli
                                self.firstLocation = self.locations[0]
                                self.secondLocation = self.locations[1]
                                self.firstStim.parameters.position = self.experiment.stimPositions[self.firstLocation]
                                self.secondStim.parameters.position = self.experiment.stimPositions[self.secondLocation] 
                                
                                """This is what's shown on every trial"""
                                response = self.presentExperimentTrial(curBlock,trialIndex,whichPart,firstColor,secondColor)
                                
                                #for "different" trials, update the step Weibull function for the appropriate color category:
                                if self.trialListMatrix[trialIndex].sameDiff=="diff":
                                        updateColorDistance(self)
                                        
                                        
                                print str(response) + " " + str(self.curDistance) + str(firstColor) + " " + str(secondColor) + "\n"     
                        # Get final estimate.
                        #t=self.q.mean()
                        #sd=self.q.sd()
                        #self.q.beta_analysis()                 

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
#currentPresentation.getPsychometricFunctions("questNothingVsColor")
currentPresentation.getPsychometricFunctions("practice")

# Thank the subject
currentPresentation.showWrappedText(currentExp.thanks)
