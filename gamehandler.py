from direct.showbase.DirectObject import DirectObject

from camerahandler import CameraHandler


class GameHandler(DirectObject):
    destination = None

    def __init__(self, showbase, game):
        DirectObject.__init__(self)

        self.client = showbase.client
        self.game = game

        # Keys array (down if 1, up if 0)
        self.keys = {"left": 0, "right": 0, "up": 0, "down": 0, "c": 0}

        # holding c will focus the camera on clients warlock
        self.accept("c", self.setValue, [self.keys, "c", 1])
        self.accept("c-up", self.setValue, [self.keys, "c", 0])

        # mouse 1 is for casting the spell set by the keys
        # showbase.accept("mouse1", self.castSpell)

        # mouse 3 is for movement, or canceling keys for casting spell
        self.accept("mouse3", self.updateDestination)

        self.ch = CameraHandler(showbase)

        # sets the camera up behind clients warlock looking down on it from angle
        follow = self.game.centipede.head
        self.ch.setTarget(follow.getPos().getX(), follow.getPos().getY(), follow.getPos().getZ())
        self.ch.turnCameraAroundPoint(follow.getH(), 0)

    def setValue(self, array, key, value):
        array[key] = value

    # sends destination request to server, or cancels spell if selected
    def updateDestination(self):
        destination = self.ch.getMouse3D()
        if not destination.getZ() == -1:
            self.client.sendData(('updateDest', (destination.getX(), destination.getY())))

    def updateCamera(self, dt):
        # sets the camMoveTask to be run every frame
        self.ch.camMoveTask(dt)

        # if c is down update camera to always be following on the warlock
        if self.keys["c"]:
            follow = self.game.centipede.head
            self.ch.setTarget(follow.getPos().getX(), follow.getPos().getY(), follow.getPos().getZ())
            self.ch.turnCameraAroundPoint(0, 0)

    def update(self, dt):
        self.updateCamera(dt)

    def destroy(self):
        self.ignoreAll()
        self.ch.destroy()
