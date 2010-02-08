# -*- coding: utf-8 -*-
'''environment.py
Classes responsible for environment such as terrain, lighting, skyboxes, etc.
'''
from direct.showbase import DirectObject
#from panda3d.core import AmbientLight, DirectionalLight, VBase4
# For TerrainManager
#from panda3d.core import CardMaker, NodePath, GeomNode, GeoMipTerrain,  PNMImage, StringStream, TextureStage, Vec3, Vec4, VBase3D, Texture
#from panda3d.core import CardMaker, TransparencyAttrib, BitMask32, Plane, Point3, PlaneNode, CullFaceAttrib

from pandac.PandaModules import AmbientLight, DirectionalLight, VBase4, CardMaker, NodePath, GeomNode, GeoMipTerrain,  PNMImage, StringStream, TextureStage, Vec3, Vec4, VBase3D, Texture, CardMaker, TransparencyAttrib, BitMask32, Plane, Point3, PlaneNode, CullFaceAttrib

import gui
import water
picker = gui.getPicker()

class Lights:
    def __init__(self, lightsOn=True,showLights=False):        
        #Initialize bg colour
        colour = (0,0,0)
        base.setBackgroundColor(*colour)
        
        if lightsOn==False: return
        
        # Initialise lighting
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(0.25, 0.25, 0.25, 1))
        self.alnp = render.attachNewNode(self.alight)
        render.setLight(self.alnp)
        
        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(1.0, 1.0, 1.0, 1))
        self.dlnp = render.attachNewNode(self.dlight)
        self.dlnp.setHpr(45, -45, 32)
        render.setLight(self.dlnp)
        
        
class SkyManager(DirectObject.DirectObject):
    def __init__(self):
        self.att_skybox = water.SkyDome2(render)
        self.att_skybox.setStandardControl()
        #taskMgr.add(self.updateSky, "updateSky")
    
    def updateSky(self, task):
        pass
        

class TerrainManager(DirectObject.DirectObject):
    def __init__(self):
        self.accept("mouse1", self.lclick)
        self.waterType = 2
        self.water = None
        self.citycolors = {0: VBase3D(1, 1, 1)}
        self.accept("h", self.switchWater)
        
        self.accept('generateRegion', self.generateWorld)
        self.accept("regionView_normal", self.setSurfaceTextures)
        self.accept("regionView_owners", self.setOwnerTextures)
        self.accept("regionView_foundNew", self.regionViewFound)
        self.accept("updateRegion", self.updateRegion)
        
        # View: 0, region, # cityid
        self.view = 0
        self.ownerview = False
    
    def lclick(self):
        cell = picker.getMouseCell()
        print "Cell:", cell
        if not self.view:
            messenger.send("clickForCity", [cell])
    
    def switchWater(self):
        print "Switch Water"
        self.waterType += 1
        if self.waterType > 2:
            self.waterType = 0
        self.generateWater(self.waterType)
    
    def generateWorld(self, heightmap, tiles, cities, container):
        self.heightmap = heightmap
        self.terrain = GeoMipTerrain("surface")
        self.terrain.setFocalPoint(base.camera)
        self.terrain.setHeightfield(self.heightmap)
        self.terrain.setFocalPoint(base.camera)
        self.terrain.setBlockSize(64)
        self.terrain.generate()

        root = self.terrain.getRoot()
        root.reparentTo(render)
        root.setSz(100)
        messenger.send('makePickable', [root])   
        
        if self.heightmap.getXSize() > self.heightmap.getYSize():
            self.size = self.heightmap.getXSize()-1
        else:
            self.size = self.heightmap.getYSize()-1
                
        # Set multi texture
        # Source http://www.panda3d.org/phpbb2/viewtopic.php?t=4536
        self.generateSurfaceTextures()
        self.generateOwnerTexture(tiles, cities)
                
        self.setSurfaceTextures()
        self.generateWater(2)
        taskMgr.add(self.updateTerrain, "updateTerrain")
        print "Done with terrain generation"
        messenger.send("finishedTerrainGen")
    
    def generateColorMap(self):
        print "GenerateColorMap"
        colormap = PNMImage(self.heightmap.getXSize(), self.heightmap.getYSize())
        colormap.addAlpha()
        slopemap = self.terrain.makeSlopeImage()
        
        # Iterate through every pix of color map. This will be very slow so until faster method is developed, use sparingly
        # getXSize returns pixles length starting with 1, subtract 1 for obvious reasons
        for x in range(0, self.heightmap.getXSize()-1):
            for y in range(0, colormap.getYSize()-1):
                # Else if statements used to make sure one channel is used per pixel
                # Also for some optimization
                # Snow. We do things funky here as alpha will be 1 already.
                if self.heightmap.getGrayVal(x, y) < 200:
                    colormap.setAlpha(x, y, 0)
                else:
                    colormap.setAlpha(x, y, 1)
                # Beach. Estimations from http://www.simtropolis.com/omnibus/index.cfm/Main.SimCity_4.Custom_Content.Custom_Terrains_and_Using_USGS_Data
                if self.heightmap.getGrayVal(x,y) < 62:
                    colormap.setBlue(x, y, 1)
                # Rock
                elif slopemap.getGrayVal(x, y) > 170:
                    colormap.setRed(x, y, 1)
                else:
                    colormap.setGreen(x, y, 1)
        return colormap
    
    def generateOwnerTexture(self, tiles, cities):
        '''Generates a simple colored texture to be applied to the city info region overlay.
        Due to different coordinate systems (terrain org bottom left, texture top left)
        some conversions are needed,
        
        Also creates and sends a citylabels dict for the region view
        '''
        self.citymap = PNMImage(self.size, self.size)
        citylabels = cities
        scratch = {}
        import random
        # Setup for city labels
        for ident in cities:
            scratch[ident] = []
        
        # conversion for y axis
        ycon = []
        s = self.size - 1
        for y in range(self.size):
            ycon.append(s)
            s -= 1
        for ident, city in cities.items():
            if ident not in self.citycolors:
                self.citycolors[ident] = VBase3D(random.random(), random.random(), random.random())
        for tile in tiles:
            # X Y is flipped with a converter. Too tired to figure out why,
            self.citymap.setXel(tile.coords[1], ycon[tile.coords[0]], self.citycolors[tile.cityid])
            # Scratch for labeling
            if tile.cityid:
                scratch[tile.cityid].append((tile.coords[0], tile.coords[1]))
        for ident, values in scratch.items():
            xsum = 0
            ysum = 0
            n = 0
            for coords in values:
                xsum += coords[0]
                ysum += coords[1]
                n += 1
            xavg = xsum/n
            yavg = ysum/n
            citylabels[ident]["position"] = (xavg, yavg)
        messenger.send("updateCityLabels", [citylabels, self.terrain])
    
    def generateSurfaceTextures(self):
        colormap = self.generateColorMap()
        
        self.colorTexture = Texture()
        self.colorTexture.load(colormap)
        self.colorTS = TextureStage('color')
        self.colorTS.setSort(0)
        self.colorTS.setPriority(1)
        
        # Textureize
        self.grassTexture = loader.loadTexture("Textures/grass.png")
        self.grassTS = TextureStage('grass')
        self.grassTS.setSort(1)
        
        self.rockTexture = loader.loadTexture("Textures/rock.jpg")
        self.rockTS = TextureStage('rock')
        self.rockTS.setSort(2)
        self.rockTS.setCombineRgb(TextureStage.CMAdd, TextureStage.CSLastSavedResult, TextureStage.COSrcColor, TextureStage.CSTexture, TextureStage.COSrcColor)
        
        self.sandTexture = loader.loadTexture("Textures/sand.jpg")
        self.sandTS = TextureStage('sand')
        self.sandTS.setSort(3)
        self.sandTS.setPriority(5)
        
        self.snowTexture = loader.loadTexture("Textures/ice.png")
        self.snowTS = TextureStage('snow')
        self.snowTS.setSort(4)
        self.snowTS.setPriority(0)
        
        # Grid for city placement and guide and stuff
        self.gridTexture = loader.loadTexture("Textures/grid.png")
        self.gridTexture.setWrapU(Texture.WMRepeat)
        self.gridTexture.setWrapV(Texture.WMRepeat)
        self.gridTS = TextureStage('grid')
        self.gridTS.setSort(5)
        self.gridTS.setPriority(10)
    
    def newTerrainOverlay(self, task):
        root = self.terrain.getRoot()
        position = picker.getMouseCell()
        if position:
            # Check to make sure we do not go out of bounds
            if position[0] < 16:
                position = (16, position[1])
            elif position[0] > self.size-16:
                position = (self.size-16, position[1])
            if position[1] < 16:
                position = (position[0], 16)
            elif position [1] > self.size-16:
                position = (position[0], self.size-16)                
            root.setTexOffset(self.tileTS, -float(position[0]-16)/32, -float(position[1]-16)/32)
        return task.cont
    
    def regionViewFound(self):
        print "RegionViewFound"
        '''Gui for founding a new city!'''
        self.setOwnerTextures()
        root = self.terrain.getRoot()
        task = taskMgr.add(self.newTerrainOverlay, "newTerrainOverlay")
        tileTexture = loader.loadTexture("Textures/tile.png")
        tileTexture.setWrapU(Texture.WMClamp)
        tileTexture.setWrapV(Texture.WMClamp)
        self.tileTS = TextureStage('tile')
        self.tileTS.setSort(6)
        #self.tileTS.setMode(TextureStage.MBlend)
        self.tileTS.setMode(TextureStage.MDecal)
        #self.tileTS.setColor(Vec4(1,0,1,1))
        root.setTexture(self.tileTS, tileTexture)
        root.setTexScale(self.tileTS, self.size/32, self.size/32)
        self.acceptOnce("mouse1", self.regionViewFound2)
        self.acceptOnce("escape", self.cancelRegionViewFound)
    
    def regionViewFound2(self):
        '''Grabs cell location for founding.
        The texture coordinate is used as the mouse may enter an out of bounds area.
        '''
        print "RegionViewFound2"
        root = self.terrain.getRoot()
        root_position = root.getTexOffset(self.tileTS)
        # We offset the position of the texture, so we will now put the origin of the new city not on mouse cursor but the "bottom left" of it. Just need to add 32 to get other edge
        position = [int(abs(root_position[0]*32)), int(abs(root_position[1]*32))]
        self.cancelRegionViewFound()
        messenger.send("found_city_name", [position])
    
    def cancelRegionViewFound(self):
        print "CancelRegionViewFound"
        taskMgr.remove("newTerrainOverlay")
        root = self.terrain.getRoot()
        root.clearTexture(self.tileTS)
        # Restore original mouse function
        self.accept("mouse1", self.lclick)
        #messenger.send("showRegionGUI")
    
    def setSurfaceTextures(self):
        self.ownerview = False
        root = self.terrain.getRoot()
        root.clearTexture()
        root.setTexture( self.colorTS, self.colorTexture ) 
        root.setTexture( self.grassTS, self.grassTexture )
        root.setTexScale(self.grassTS, self.size, self.size) 
        root.setTexture( self.rockTS, self.rockTexture ) 
        root.setTexScale(self.rockTS, self.size, self.size) 
        root.setTexture( self.sandTS, self.sandTexture) 
        root.setTexScale(self.sandTS, self.size, self.size) 
        root.setTexture( self.snowTS, self.snowTexture ) 
        root.setTexScale(self.snowTS, self.size, self.size) 
        root.setTexture( self.gridTS, self.gridTexture ) 
        root.setTexScale(self.gridTS, self.size, self.size)
        
        root.setShaderInput('size', self.size, self.size, self.size, self.size)
        root.setShader(loader.loadShader('Shaders/terraintexture.sha'))
    
    def setOwnerTextures(self):
        self.ownerview = True
        root = self.terrain.getRoot()
        root.clearShader()
        root.clearTexture()
        cityTexture = Texture()
        cityTexture.load(self.citymap)
        cityTS = TextureStage('citymap')
        cityTS.setSort(0)
        root.setTexture( self.gridTS, self.gridTexture ) 
        root.setTexScale(self.gridTS, self.size, self.size)
        print "Updating ownership graphics"
        root.setTexture(cityTS, cityTexture, 1)
    
    def updateRegion(self, heightmap, tiles, cities):
        self.generateOwnerTexture(tiles, cities)
        if self.ownerview:
            self.setOwnerTextures()
    
    def updateTerrain(self, task):
        '''Updates terrain and water'''
        self.terrain.update()
        # Water
        if self.waterType is 2:
            pos = base.camera.getPos()
            render.setShaderInput('time', task.time)
            mc = base.camera.getMat( )
            self.water.changeCameraPos(pos,mc)
            self.water.changeCameraPos(pos,mc)
        #print "Render diagnostics"
        #render.analyze()
        #base.cTrav.showCollisions(render)
        return task.cont 
    
    def generateWater(self, style):
        print "Generate Water"
        '''Generates water
        style 0: blue card
        style 1: reflective card
        style 2: reflective card with shaders
        '''
        if self.water:
            self.water.removeNode()
        if style is 0:
            cm = CardMaker("water")
            cm.setFrame(-1, 1, -1, 1)
            cm.setColor(0, 0, 1, 0.9)
            self.water = render.attachNewNode(cm.generate())
            self.water.setScale(self.size)
            self.water.lookAt(0, 0, -1)
            self.water.setZ(22)
            messenger.send('makePickable', [self.water])
        elif style is 1:
            # From Prosoft's super awesome terrain demo
            cm = CardMaker("water")
            cm.setFrame(-1, 1, -1, 1)
            self.water = render.attachNewNode(cm.generate())
            self.water.setScale(self.size)
            self.water.lookAt(0, 0, -1)
            self.water.setZ(22)
            self.water.setShaderOff(1)
            self.water.setLightOff(1)
            self.water.setAlphaScale(0.5)
            self.water.setTransparency(TransparencyAttrib.MAlpha)
            wbuffer = base.win.makeTextureBuffer("water", 512, 512)
            wbuffer.setClearColorActive(True)
            wbuffer.setClearColor(base.win.getClearColor())
            self.wcamera = base.makeCamera(wbuffer)
            self.wcamera.reparentTo(render)
            self.wcamera.node().setLens(base.camLens)
            self.wcamera.node().setCameraMask(BitMask32.bit(1))
            self.water.hide(BitMask32.bit(1))
            wtexture = wbuffer.getTexture()
            wtexture.setWrapU(Texture.WMClamp)
            wtexture.setWrapV(Texture.WMClamp)
            wtexture.setMinfilter(Texture.FTLinearMipmapLinear)
            self.wplane = Plane(Vec3(0, 0, 1), Point3(0, 0, self.water.getZ()))
            wplanenp = render.attachNewNode(PlaneNode("water", self.wplane))
            tmpnp = NodePath("StateInitializer")
            tmpnp.setClipPlane(wplanenp)
            tmpnp.setAttrib(CullFaceAttrib.makeReverse())
            self.wcamera.node().setInitialState(tmpnp.getState())
            self.water.projectTexture(TextureStage("reflection"), wtexture, self.wcamera)
            messenger.send('makePickable', [self.water])
        elif style is 2:
            # From Clcheung just as super awesome demomaster
            self.water_level = Vec4(0.0, 0.0, 22.0, 1.0)
            self.water = water.WaterNode(0, 0, self.size, self.size, self.water_level.getZ())
            self.water.setStandardControl()
            self.water.changeParams(None)
            wl=self.water_level
            wl.setZ(wl.getZ()-0.05)
            #root.setShaderInput('waterlevel', self.water_level)
            render.setShaderInput('time', 0)
            messenger.send('makePickable', [self.water.waterNP])