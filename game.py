import random

from direct.showbase.DirectObject import DirectObject
from panda3d.core import AmbientLight
from panda3d.core import CollisionTraverser, CollisionHandlerEvent
from panda3d.core import LVector3
from panda3d.core import PointLight

from centipede import Centipede
from food import Food
from world import World


class Game(DirectObject):
    def __init__(self, showbase, usersData, gameData):
        DirectObject.__init__(self)

        self.showbase = showbase
        self.usersData = usersData
        self.gameData = gameData

        random.seed(self.gameData.randSeed)

        # Initialize the collision traverser.
        self.cTrav = CollisionTraverser()

        # Initialize the handler.
        self.collHandEvent = CollisionHandlerEvent()
        self.collHandEvent.addInPattern('into-%in')

        self.world = World(showbase)

        self.ambientLight = showbase.render.attachNewNode(AmbientLight("ambientLight"))
        # Set the color of the ambient light
        self.ambientLight.node().setColor((.1, .1, .1, 1))
        # add the newly created light to the lightAttrib
        # showbase.render.setLight(self.ambientLight)

        self.spotlight = None

        numberOfPlayers = len(self.usersData)
        for index, user in enumerate(self.usersData):
            user.centipede = Centipede(showbase, index, numberOfPlayers, self.addToCollisions)
            if user.thisPlayer:
                self.centipede = user.centipede
                self.centipede.attachRing(showbase)

                self.spotlight = self.centipede.head.attachNewNode(PointLight("playerSpotlight"))
                self.spotlight.setPos(LVector3(0, 0, 8))
                # Now we create a spotlight. Spotlights light objects in a given cone
                # They are good for simulating things like flashlights
                self.spotlight.node().setAttenuation(LVector3(.025, 0.0005, 0.0001))
                self.spotlight.node().setColor((0.35, 0.35, .35, 1))
                self.spotlight.node().setSpecularColor((0.01, 0.01, 0.01, 1))

                showbase.render.setLight(self.spotlight)

        self.perPixelEnabled = True
        self.shadowsEnabled = True
        #if self.spotlight:
        #    self.spotlight.node().setShadowCaster(True, 512, 512)
        showbase.render.setShaderAuto()

        self.foods = []
        for i in range(self.gameData.maxFoods):
            self.foods.append(Food(self.showbase, i, self.addToCollisions))

    def destroy(self):
        self.ignoreAll()
        self.collHandEvent.clear()
        self.ambientLight.removeNode()
        self.world.destroy()
        for user in self.usersData:
            user.centipede.destroy()
        for food in self.foods:
            food.destroy()

    def runTick(self, dt, tick):
        # run each of the centipedes simulations
        for user in self.usersData:
            user.centipede.update(dt)
            headPosition = user.centipede.head.getPos()
            if abs(headPosition.x) > 123 or abs(headPosition.y) > 123:
                user.centipede.reset()
            if len(user.centipede.body) > 10:
                return False

        for food in self.foods:
            food.update(dt)

        self.cTrav.traverse(self.showbase.render)

        # Return true if game is still not over (false to end game)
        return True

    def collideInto(self, collEntry):
        print "collide into"
        fromInto = collEntry.getFromNodePath().node().getIntoCollideMask()
        intoInto = collEntry.getIntoNodePath().node().getIntoCollideMask()
        fromIntoIndex = fromInto.getLowestOnBit() - 1
        intoIntoIndex = intoInto.getLowestOnBit() - 1

        # Collision was with a Food!
        if intoIntoIndex == -1:
            # TODO: Get food better
            for food in self.foods:
                if collEntry.getIntoNodePath() == food.model.collisionNode[0]:
                    user = self.usersData[fromIntoIndex]
                    user.centipede.addLength(self.showbase)
                    food.reset()
                    print "om nommed a food"
                    return

        # Centipede eating themself
        if fromIntoIndex == intoIntoIndex:
            print "hitting self"
            user = self.usersData[fromIntoIndex]
            if len(user.centipede.body) > 2:
                if collEntry.getIntoNodePath() == user.centipede.tail.collisionNode[0]:
                    user.centipede.reset()
                    print "dieded self tail"
                    return
                for i in range(len(user.centipede.body) - 1 - 2):
                    if collEntry.getIntoNodePath() == user.centipede.body[i + 2].collisionNode[0]:
                        user.centipede.reset()
                        print "dieded self body", i
                        return
        else:
            # TODO: Check for both heads
            # if bothHeads:
            # one will survive if it's angle to the other node is greater than 90degrees from straight ahead

            # Centipede eating another centipede
            crasher = self.usersData[fromIntoIndex]
            crasher.centipede.reset()

            # Give crashee a point on behalf of crasher
            crashee = self.usersData[intoIntoIndex]
            print "Player", intoIntoIndex, " gets a point!"
            # crashee.point += 1

    def addToCollisions(self, item):
        # Add this object to the traverser.
        self.cTrav.addCollider(item[0], self.collHandEvent)

        # Accept the events sent by the collisions.
        self.accept('into-' + str(item[1]), self.collideInto)
