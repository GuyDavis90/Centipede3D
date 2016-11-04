import math

from direct.showbase.DirectObject import DirectObject
from panda3d.core import Vec2, Vec3, Point3, Plane
from panda3d.core import WindowProperties


# Last modified: 10/2/2009
# This class takes over control of the camera and sets up a Real Time Strategy game type camera control system. The user can move the camera three 
# ways. If the mouse cursor is moved to the edge of the screen, the camera will pan in that direction. If the right mouse button is held down, the 
# camera will orbit around it's target point in accordance with the mouse movement, maintaining a fixed distance. The mouse wheel will move the 
# camera closer to or further from it's target point. 

# This code was originally developed by Ninth from the Panda3D forums, and has been modified by piratePanda to achieve a few effects. 
# First mod: Comments. I've gone through the code and added comments to explain what is doing what, and the reason for each line of code. 
# Second mod: Name changes. I changed some names of variables and functions to make the code a bit more readable (in my opinion). 
# Third mod: Variable pan rate. I have changed the camera panning when the mouse is moved to the edge of the screen so that the panning 
# rate is dependant on the distance the camera has been zoomed out. This prevents the panning from appearing faster when 
# zoomed in than when zoomed out. I have also added a pan rate variable, which could be modified by an options menu, so it is 
# easier to give the player control over how fast the camera pans. 
# Fourth mod: Variable pan zones. I added a variable to control the size of the zones at the edge of the screen where the camera starts 
# panning. 
# Fifth mod: Orbit limits: I put in a system to limit how far the camera can move along it's Y orbit to prevent it from moving below the ground 
# plane or so high that you get a fast rotation glitch. 
# Sixth mod: Pan limits: I put in variables to use for limiting how far the camera can pan, so the camera can't pan away from the map. These 
# values will need to be customized to the map, so I added a function for setting them. 

# TODO: Provide better interface for controlling the camera
class CameraHandler(DirectObject):
    def __init__(self, showbase):
        DirectObject.__init__(self)

        self.showbase = showbase
        self.showbase.disableMouse()
        # This disables the default mouse based camera control used by panda. This default control is awkward, and won't be used.

        self.showbase.camera.setPos(0, -150, 200)
        self.showbase.camera.lookAt(0, 0, 0)
        # Gives the camera an initial position and rotation.

        self.mx, self.my = 0, 0
        # Sets up variables for storing the mouse coordinates

        self.orbiting = False
        # A boolean variable for specifying whether the camera is in orbiting mode. Orbiting mode refers to when the camera is being moved
        # because the user is holding down the right mouse button.

        self.target = Vec3()
        # sets up a vector variable for the camera's target. The target will be the coordinates that the camera is currently focusing on.

        self.camDist = 150
        # A variable that will determine how far the camera is from it's target focus

        self.panRateDivisor = 10
        # This variable is used as a divisor when calculating how far to move the camera when panning. Higher numbers will yield slower panning
        # and lower numbers will yield faster panning. This must not be set to 0.

        self.panZoneSize = .1
        # This variable controls how close the mouse cursor needs to be to the edge of the screen to start panning the camera. It must be less than 1,
        # and I recommend keeping it less than .2

        self.panLimitsX = Vec2(-1000, 1000)
        self.panLimitsY = Vec2(-1000, 1000)
        # These two vairables will serve as limits for how far the camera can pan, so you don't scroll away from the map.

        self.maxZoomOut = 500
        self.maxZoomIn = 25
        # These two variables set the max distance a person can zoom in or out

        self.orbitRate = 75
        # This is the rate of speed that the camera will rotate when middle mouse is pressed and mouse moved
        # recommended rate 50-100

        self.setTarget(0, 0, 0)
        # calls the setTarget function to set the current target position to the origin.

        self.turnCameraAroundPoint(0, 0)
        # calls the turnCameraAroundPoint function with a turn amount of 0 to set the camera position based on the target and camera distance

        self.accept("mouse2", self.startOrbit)
        # sets up the camrea handler to accept a right mouse click and start the "drag" mode.

        self.accept("mouse2-up", self.stopOrbit)
        # sets up the camrea handler to understand when the right mouse button has been released, and ends the "drag" mode when
        # the release is detected.

        self.storeX = 0
        self.storeY = 0
        # for storing of the x and y for the orbit

        # The next pair of lines use lambda, which creates an on-the-spot one-shot function.

        self.accept("wheel_up", self.zoomIn)
        # sets up the camera handler to detet when the mouse wheel is rolled upwards and uses a lambda function to call the
        # adjustCamDist function  with the argument 0.9

        self.accept("wheel_down", self.zoomOut)
        # sets up the camera handler to detet when the mouse wheel is rolled upwards and uses a lambda function to call the
        # adjustCamDist function  with the argument 1.1

        # Keys array (down if 1, up if 0)
        self.keys = {"cam-left": 0, "cam-right": 0, "cam-up": 0, "cam-down": 0}

        # Using Arrow Keys
        self.accept("arrow_left", self.setValue, [self.keys, "cam-left", 1])
        self.accept("arrow_right", self.setValue, [self.keys, "cam-right", 1])
        self.accept("arrow_up", self.setValue, [self.keys, "cam-up", 1])
        self.accept("arrow_down", self.setValue, [self.keys, "cam-down", 1])
        self.accept("arrow_left-up", self.setValue, [self.keys, "cam-left", 0])
        self.accept("arrow_right-up", self.setValue, [self.keys, "cam-right", 0])
        self.accept("arrow_up-up", self.setValue, [self.keys, "cam-up", 0])
        self.accept("arrow_down-up", self.setValue, [self.keys, "cam-down", 0])

        self.keyPanRate = 1.5
        # pan rate for when user presses the arrow keys

        # set up plane for checking collision with for mouse-3d world
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))

    def destroy(self):
        self.ignoreAll()

    def setValue(self, array, key, value):
        array[key] = value

    def clamp(self, val, minVal, maxVal):
        val = min(max(val, minVal), maxVal)
        return val

    def zoomOut(self):
        if self.camDist <= self.maxZoomOut:
            self.adjustCamDist(1.1)
        return True

    def zoomIn(self):
        if self.camDist >= self.maxZoomIn:
            self.adjustCamDist(0.9)
        return True

    def turnCameraAroundPoint(self, deltaX, deltaY):
        # This function performs two important tasks. First, it is used for the camera orbital movement that occurs when the
        # right mouse button is held down. It is also called with 0s for the rotation inputs to reposition the camera during the
        # panning and zooming movements.
        # The delta inputs represent the change in rotation of the camera, which is also used to determine how far the camera
        # actually moves along the orbit.

        newCamHpr = Vec3()
        newCamPos = Vec3()
        # Creates temporary containers for the new rotation and position values of the camera.

        camHpr = self.showbase.camera.getHpr()
        # Creates a container for the current HPR of the camera and stores those values.

        newCamHpr.setX(camHpr.getX() + deltaX)
        newCamHpr.setY(self.clamp(camHpr.getY() - deltaY, -85, -10))
        newCamHpr.setZ(camHpr.getZ())
        # Adjusts the newCamHpr values according to the inputs given to the function. The Y value is clamped to prevent
        # the camera from orbiting beneath the ground plane and to prevent it from reaching the apex of the orbit, which
        # can cause a disturbing fast-rotation glitch.

        self.showbase.camera.setHpr(newCamHpr)
        # Sets the camera's rotation to the new values.

        angleradiansX = newCamHpr.getX() * (math.pi / 180.0)
        angleradiansY = newCamHpr.getY() * (math.pi / 180.0)
        # Generates values to be used in the math that will calculate the new position of the camera.

        newCamPos.setX(self.camDist * math.sin(angleradiansX) * math.cos(angleradiansY) + self.target.getX())
        newCamPos.setY(-self.camDist * math.cos(angleradiansX) * math.cos(angleradiansY) + self.target.getY())
        newCamPos.setZ(-self.camDist * math.sin(angleradiansY) + self.target.getZ())
        self.showbase.camera.setPos(newCamPos.getX(), newCamPos.getY(), newCamPos.getZ())
        # Performs the actual math to calculate the camera's new position and sets the camera to that position.
        # Unfortunately, this math is over my head, so I can't fully explain it.

        self.showbase.camera.lookAt(self.target.getX(), self.target.getY(), self.target.getZ())

    # Points the camera at the target location.

    def getTarget(self):
        return self.target

    # returns the cur

    def setTarget(self, x, y, z):
        # This function is used to give the camera a new target position.
        x = self.clamp(x, self.panLimitsX.getX(), self.panLimitsX.getY())
        self.target.setX(x)
        y = self.clamp(y, self.panLimitsY.getX(), self.panLimitsY.getY())
        self.target.setY(y)
        self.target.setZ(z)

    # Stores the new target position values in the target variable. The x and y values are clamped to the pan limits.

    def setPanLimits(self, xMin, xMax, yMin, yMax):
        # This function is used to set the limitations of the panning movement.

        self.panLimitsX = (xMin, xMax)
        self.panLimitsY = (yMin, yMax)

    # Sets the inputs into the limit variables.

    def startOrbit(self):
        # This function puts the camera into orbiting mode.

        # Get windows properties
        props = WindowProperties()
        # Set Hide Cursor Property
        # props.setCursorHidden(True)
        # Set properties
        self.showbase.win.requestProperties(props)
        # hide cursor

        if self.showbase.mouseWatcherNode.hasMouse():
            # We're going to use the mouse, so we have to make sure it's in the game window. If it's not and we try to use it, we'll get
            # a crash error.
            mpos = self.showbase.mouseWatcherNode.getMouse()
            self.storeX = mpos.getX()
            self.storeY = mpos.getY()
        # take current cursor values

        self.showbase.win.movePointer(0, self.showbase.win.getXSize() / 2, self.showbase.win.getYSize() / 2)
        # set to center
        self.mx = 0
        self.my = 0

        self.orbiting = True

    # Sets the orbiting variable to true to designate orbiting mode as on.

    def stopOrbit(self):
        # This function takes the camera out of orbiting mode.

        self.orbiting = False
        # Sets the orbiting variable to false to designate orbiting mode as off.

        self.showbase.win.movePointer(0, int((self.storeX + 1.0) / 2 * self.showbase.win.getXSize()), int(
            self.showbase.win.getYSize() - ((self.storeY + 1.0) / 2 * self.showbase.win.getYSize())))
        # set to taken cursor values from startOrbit
        if self.showbase.mouseWatcherNode.hasMouse():
            # We're going to use the mouse, so we have to make sure it's in the game window. If it's not and we try to use it, we'll get
            # a crash error.
            mpos = self.showbase.mouseWatcherNode.getMouse()
            self.mx = mpos.getX()
            self.my = mpos.getY()

        # Get windows properties
        props = WindowProperties()
        # Set Hide Cursor Property
        props.setCursorHidden(False)
        # Set properties
        self.showbase.win.requestProperties(props)

    # reshow cursor

    def adjustCamDist(self, distFactor):
        # This function increases or decreases the distance between the camera and the target position to simulate zooming in and out.
        # The distFactor input controls the amount of camera movement.
        # For example, inputing 0.9 will set the camera to 90% of it's previous distance.

        self.camDist = self.camDist * distFactor
        # Sets the new distance into self.camDist.

        self.turnCameraAroundPoint(0, 0)

    # Calls turnCameraAroundPoint with 0s for the rotation to reset the camera to the new position.

    def camMoveTask(self, dt):
        # This task is the camera handler's work house. It's set to be called every frame and will control both orbiting and panning the camera.

        if self.showbase.mouseWatcherNode.hasMouse():
            # We're going to use the mouse, so we have to make sure it's in the game window. If it's not and we try to use it, we'll get
            # a crash error.

            mpos = self.showbase.mouseWatcherNode.getMouse()
            # Gets the mouse position

            if self.orbiting:
                # Checks to see if the camera is in orbiting mode. Orbiting mode overrides panning, because it would be problematic if, while
                # orbiting the camera the mouse came close to the screen edge and started panning the camera at the same time.

                self.turnCameraAroundPoint((self.mx - mpos.getX()) * self.orbitRate * dt,
                                           (self.my - mpos.getY()) * self.orbitRate * dt)

            else:
                # If the camera isn't in orbiting mode, we check to see if the mouse is close enough to the edge of the screen to start panning

                moveY = False
                moveX = False
                # these two booleans are used to denote if the camera needs to pan. X and Y refer to the mouse position that causes the
                # panning. X is the left or right edge of the screen, Y is the top or bottom.

                if self.my > (1 - self.panZoneSize):
                    angleradiansX1 = self.showbase.camera.getH() * (math.pi / 180.0)
                    panRate1 = (1 - self.my - self.panZoneSize) * (self.camDist / self.panRateDivisor)
                    moveY = True
                if self.my < (-1 + self.panZoneSize):
                    angleradiansX1 = self.showbase.camera.getH() * (math.pi / 180.0) + math.pi
                    panRate1 = (1 + self.my - self.panZoneSize) * (self.camDist / self.panRateDivisor)
                    moveY = True
                if self.mx > (1 - self.panZoneSize):
                    angleradiansX2 = self.showbase.camera.getH() * (math.pi / 180.0) + math.pi * 0.5
                    panRate2 = (1 - self.mx - self.panZoneSize) * (self.camDist / self.panRateDivisor)
                    moveX = True
                if self.mx < (-1 + self.panZoneSize):
                    angleradiansX2 = self.showbase.camera.getH() * (math.pi / 180.0) - math.pi * 0.5
                    panRate2 = (1 + self.mx - self.panZoneSize) * (self.camDist / self.panRateDivisor)
                    moveX = True
                # These four blocks check to see if the mouse cursor is close enough to the edge of the screen to start panning and then
                # perform part of the math necessary to find the new camera position. Once again, the math is a bit above my head, so
                # I can't properly explain it. These blocks also set the move booleans to true so that the next lines will move the camera.

                # If up or down keys are pressed
                if self.keys["cam-up"] ^ self.keys["cam-down"]:
                    moveY = True
                    panRate1 = self.keyPanRate
                    # Update warlock position on z plane
                    if self.keys["cam-up"]:
                        angleradiansX1 = self.showbase.camera.getH() * (math.pi / 180.0) + math.pi
                    if self.keys["cam-down"]:
                        angleradiansX1 = self.showbase.camera.getH() * (math.pi / 180.0)

                # If left or right keys are pressed
                if self.keys["cam-left"] ^ self.keys["cam-right"]:
                    moveX = True
                    panRate2 = self.keyPanRate
                    # Update warlock position on x plane
                    if self.keys["cam-left"]:
                        angleradiansX2 = self.showbase.camera.getH() * (math.pi / 180.0) + math.pi * 0.5
                    if self.keys["cam-right"]:
                        angleradiansX2 = self.showbase.camera.getH() * (math.pi / 180.0) - math.pi * 0.5

                if moveY:
                    tempX = self.target.getX() + math.sin(angleradiansX1) * panRate1 * dt * 50
                    tempX = self.clamp(tempX, self.panLimitsX.getX(), self.panLimitsX.getY())
                    self.target.setX(tempX)
                    tempY = self.target.getY() - math.cos(angleradiansX1) * panRate1 * dt * 50
                    tempY = self.clamp(tempY, self.panLimitsY.getX(), self.panLimitsY.getY())
                    self.target.setY(tempY)
                    self.turnCameraAroundPoint(0, 0)
                if moveX:
                    tempX = self.target.getX() - math.sin(angleradiansX2) * panRate2 * dt * 50
                    tempX = self.clamp(tempX, self.panLimitsX.getX(), self.panLimitsX.getY())
                    self.target.setX(tempX)
                    tempY = self.target.getY() + math.cos(angleradiansX2) * panRate2 * dt * 50
                    tempY = self.clamp(tempY, self.panLimitsY.getX(), self.panLimitsY.getY())
                    self.target.setY(tempY)
                    self.turnCameraAroundPoint(0, 0)
                # These two blocks finalize the math necessary to find the new camera position and apply the transformation to the
                # camera's TARGET. Then turnCameraAroundPoint is called with 0s for rotation, and it resets the camera position based
                # on the position of the target. The x and y values are clamped to the pan limits before they are applied.
                # print self.target)
                self.mx = mpos.getX()
                self.my = mpos.getY()
                # The old mouse positions are updated to the current mouse position as the final step.

    # Finds 3d world point on the z = 0 plane for destination/target
    def getMouse3D(self):
        # make sure process has the mouse to not cause error
        if self.showbase.mouseWatcherNode.hasMouse():
            # get screen coordinates of mouse
            mpos = self.showbase.mouseWatcherNode.getMouse()
            pos3d = Point3()
            nearPoint = Point3()
            farPoint = Point3()
            # find vector of cameras facing from mouse screen coordinates and get near and far points on frustrum
            self.showbase.camLens.extrude(mpos, nearPoint, farPoint)
            # check for intersection with z = 0 plane
            if self.plane.intersectsLine(pos3d,
                                         self.showbase.render.getRelativePoint(self.showbase.camera, nearPoint),
                                         self.showbase.render.getRelativePoint(self.showbase.camera, farPoint)):
                # return this position if exists
                return pos3d
        # or return (-1, -1, -1)
        return Vec3(-1, -1, -1)
