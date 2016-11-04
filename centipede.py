from direct.actor.Actor import Actor, BitMask32
from direct.showbase.PythonUtil import fitDestAngle2Src
from panda3d.core import Vec3

from collision import initCollisionSphere


# Centipede Class
# TODO: Revisit parent class for this
class Centipede(object):
    def __init__(self, showbase, index, numPlayers, addToCollisions):
        self.addToCollisions = addToCollisions

        # Load centipede model
        self.head = Actor('models/centipede')
        # Set animation loop to Walk
        self.head.loop('Walk')
        # Reparent the model to render.
        self.head.reparentTo(showbase.render)

        self.intoMask = BitMask32.bit(index + 1)

        self.h = 360.0 / numPlayers
        self.h *= index + 1

        self.head.setH(self.h)

        self.head.setPos(self.head, 0, -100, 0)

        self.x = self.head.getX()
        self.y = self.head.getY()

        # TODO: Instead of this use node positions to "join" the centipede together
        bounds = self.head.getTightBounds()
        self.length = (bounds[1] - bounds[0]).getX() * 0.5

        # TODO: Instead of sphere for collision use something better?
        self.head.collisionNode = initCollisionSphere(self.head, 'Head', 0.65, self.intoMask, True)

        # Add head to collision detection
        addToCollisions(self.head.collisionNode)

        self.body = []

        # Load centipede model
        self.tail = Actor('models/centipede')
        # Set animation loop to Walk
        self.tail.loop('Walk')
        # Reparent the model to render.
        self.tail.reparentTo(showbase.render)

        self.tail.collisionNode = initCollisionSphere(self.tail, 'Tail', 0.65, self.intoMask)

        # Add tail to collision detection
        addToCollisions(self.tail.collisionNode)

        self.destinationNode = showbase.render.attachNewNode('Destination' + str(index))

        self.reset()

    def destroy(self):
        self.reset()
        self.head.detachNode()
        self.tail.detachNode()

    def reset(self):
        for node in self.body:
            node.detachNode()
        self.body = []
        # Set position of centipede head
        self.head.setX(self.x)
        self.head.setY(self.y)
        # Set rotation of centipede head
        self.head.setH(self.h)

        self.tail.setH(self.h)
        # Set tail position
        self.tail.setPos(self.head, 0, -self.length, 0)

        self.destinationNode.setPos(self.head, 0, 1, 0)

    def update(self, dt):
        self.updateRotation(dt)
        self.moveForwards(dt, 1.0)

    def updateRotation(self, dt):
        oldH = self.head.getH()
        self.head.headsUp(self.destinationNode)
        newH = self.head.getH()
        self.head.setH(oldH)
        newH = fitDestAngle2Src(oldH, newH)
        if newH - oldH < 0.0:
            change = -dt * 90.0
        else:
            change = dt * 90.0
        if abs(newH - oldH) < abs(change):
            self.head.setH(newH)
            self.destinationNode.setPos(self.head, 0, 1, 0)
        else:
            self.head.setH(self.head.getH() + change)

    def moveForwards(self, dt, multi):
        # Update centipede position
        self.head.setPos(self.head, 0, dt * multi * 25, 0)

        for i in range(len(self.body)):
            # Calculate new heading angle for body part
            # And update body position
            if i == 0:
                self.body[i].headsUp(self.head)
                self.body[i].setPos(self.body[i], 0, self.body[i].getDistance(self.head) - self.length, 0)
            else:
                self.body[i].headsUp(self.body[i - 1])
                self.body[i].setPos(self.body[i], 0, self.body[i].getDistance(self.body[i - 1]) - self.length, 0)
        if len(self.body) > 0:
            # Update Tail Heading
            self.tail.headsUp(self.body[len(self.body) - 1])
            # Update body position
            self.tail.setPos(self.tail, 0, self.body[len(self.body) - 1].getDistance(self.tail) - self.length, 0)
        else:
            # Update Tail Heading
            self.tail.headsUp(self.head)
            # Update body position
            self.tail.setPos(self.tail, 0, self.head.getDistance(self.tail) - self.length, 0)

    def addLength(self, showbase):
        # Load centipede model
        node = Actor('models/centipede')
        # Set animation loop to Walk
        node.loop('Walk')
        # Reparent the model to render.
        node.reparentTo(showbase.render)
        # Set body rotation
        node.setH(self.tail.getH())
        # Set body position
        node.setPos(self.tail.getPos())

        node.collisionNode = initCollisionSphere(node, 'Body-' + str(len(self.body)), 0.65, self.intoMask)

        self.addToCollisions(node.collisionNode)

        # Insert into body list
        self.body.append(node)
        # Set tail position
        self.tail.setPos(node, 0, -0.5, 0)

    # for client to attach ring below clients head
    def attachRing(self, showbase):
        self.ringNode = showbase.loader.loadModel('models/ring')
        self.ringNode.setPos(-Vec3(0, 0, 1.25))
        self.ringNode.reparentTo(self.head)

    def setDestination(self, destination):
        self.destination = Vec3(destination[0], destination[1], 0)
        self.destinationNode.setPos(self.destination)

    def getDestinationUpdate(self):
        return self.destination.getX(), self.destination.getY()
