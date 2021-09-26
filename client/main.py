# -*- coding: utf-8 -*-
title="CityMania"
#setup config file
import panda3d
from pandac.PandaModules import loadPrcFileData
loadPrcFileData( '', 'fullscreen 0')
loadPrcFileData( '', 'win-size 1024 768' )
loadPrcFileData( '', 'win-origin 450 90' )
loadPrcFileData( '', 'frame-rate-meter-scale 0.035' )
loadPrcFileData( '', 'frame-rate-meter-side-margin 0.1' )
loadPrcFileData( '', 'show-frame-rate-meter 1' )

loadPrcFileData( '', 'notify-level-util error' )
loadPrcFileData( '', 'window-title '+title )

#loadPrcFileData( '', 'want-pstats 1')
#loadPrcFileData( '', 'task-timer-verbose 1')
#loadPrcFileData( '', 'pstats-tasks 1')

#loadPrcFileData("", "interpolate-frames 1")
#loadPrcFileData("", "clock-mode limited")
#loadPrcFileData("", "clock-frame-rate 25")

loadPrcFileData("", "sync-video 0")

loadPrcFileData("", "audio-library-name p3openal_audio")

#import panda modules
import direct.directbase.DirectStart
from direct.showbase import DirectObject
from direct.interval.IntervalGlobal import *
from direct.fsm import FSM
from direct.gui.DirectGui import *
from direct.task.Task import Task
from direct.stdpy.file import *

#import python modules
import sys, subprocess, math
sys.path.append("../..")
import logging
logger = logging.getLogger('client')
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
stream = logging.StreamHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
stream.setFormatter(formatter)
logger.addHandler(stream)

import gui
import network
from CityMania.common.tile import Tile
import vfs
import region
import water
import access
import environment
import controllers
import camera
from direct.directnotify.DirectNotify import DirectNotify
notify = DirectNotify().newCategory("main")

picker = gui.getPicker()

class World(DirectObject.DirectObject):
    def __init__(self):
        """initialize"""
        self.server = None
        self.language = 'english'
        self.singlePlayer = False
        self.accept('exit', self.exit)
        self.accept('setSelfAccess', self.setSelf)
        self.accept("finishedTerrainGen", self.setupRig)
        
        base.disableMouse()
        
        base.setFrameRateMeter(True)
        self.keys()
        
        # Initialize classes
        lights = environment.Lights(lightsOn = True, showLights = True)
        
        self.terrainManager = environment.TerrainManager()
    
    def keys(self):
        """keys"""
        base.accept("f", base.toggleWireframe)
        self.accept('t',self.toggleTexture)
        #self.accept('s',self.snapShot)
    
    def snapShot(self):
        base.screenshot("Snapshot")
    
    def toggleTexture(self):
        base.toggleTexture()

    def exit(self):
        #messenger.send("sendData", ['killServerRequest'])
        #base.closeWindow(base.win)
        sys.exit()
    
    def setSelf(self, level, name):
        '''Sets the user access level and name'''
        access.level = level
        access.username = name
    
    def setupRig(self, size):
        cam = camera.Camera(size, self.terrainManager.terrain)
        sky = environment.SkyManager()
        

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(vfs.getHome() + "Logs/client.raw", "w")
        #print vfs.vfs.ls('.')
        #self.log = open('Logs/client.raw', 'w')
        notify.info('Log file initiated')

    def write(self, message):
        #return
        self.terminal.write(message)
        self.log.write(message)  
        
    def close(self):
        self.log.close()

def loadMod(name):
    """
    Loads the designated mod into memory, will require some helper functions in other classes
    """

def main(var = None):
    # Create the directories
    #filesystem.home(oo = True)
    #print "Path:", filesystem.home()

    #LOG_FILENAME = 'client.log'
    #logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
    vfs.createVFS()
    sys.stdout = Logger()
    
    connection = network.ServerSocket()
    
    script = gui.Script()
    #messenger.toggleVerbose()

    #audioManager = Audio.AudioManager()

    world=World()
    guiController = gui.GUIController(script)
    guiController.makeMainMenu()
    serverHost = 'localhost'
    serverPort = 52003
    reg = region.Region()
    kmcontroller = controllers.KMController()
    run()

if __name__ == '__main__':
    main()

#if __name__ == 'main':
#    main()

def getWorld():
    return world
