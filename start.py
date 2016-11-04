from direct.gui.DirectGui import DGG
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectEntry
from direct.gui.OnscreenText import OnscreenText, Vec3, TextNode
from direct.showbase.DirectObject import DirectObject

from client import Client


class Start(DirectObject):
    def __init__(self, main):
        DirectObject.__init__(self)

        self.showbase = main

        self.background = DirectFrame(
            frameSize=(-1, 1, -1, 1),
            frameTexture='media/gui/login/bg.png',
            parent=self.showbase.render2d,
        )

        self.username = "H3LLB0Y"
        self.server = "localhost"

        self.loginScreen("Press 'Enter' to login")
        # draws the login screen

        self.usernameBox['focus'] = 1
        # sets the cursor to the username field by default

        self.accept('tab', self.cycleLoginBox)
        self.accept('shift-tab', self.cycleLoginBox)
        # enables the user to cycle through the text fields with the tab key
        # this is a standard feature on most login forms

        self.accept('enter', self.attemptConnect)
        # submits the login form, or you can just click the Login button

        # checking variable to stop multiple presses of the button spawn multiple tasks
        self.requestAttempt = False

        self.updateStatus("Type Server and Connect!")

    def cleanup(self):
        self.ignoreAll()
        self.removeAllTasks()

        self.background.destroy()
        self.usernameText.destroy()
        self.usernameBox.destroy()
        self.serverText.destroy()
        self.serverBox.destroy()
        self.loginButton.destroy()
        self.quitButton.destroy()
        self.statusText.destroy()

    def loginScreen(self, statusText):
        # creates a basic login screen that asks for a username/password

        boxloc = Vec3(0.0, 0.0, 0.0)
        # all items in the login form will have a position relative to this
        # this makes it easier to shift the entire form around once we have
        # some graphics to display with it without having to change the
        # positioning of every form element

        # p is the position of the form element relative to the boxloc
        # coordinates set above it is changed for every form element
        p = boxloc + Vec3(-0.22, 0.09, 0.0)
        self.usernameText = OnscreenText(text="Username:", pos=p, scale=0.05, bg=(0, 0, 0, 1), fg=(1, 1, 1, 1),
                                         align=TextNode.ARight)
        # "Username: " text that appears beside the username box

        p = boxloc + Vec3(-0.2, 0.0, 0.09)
        self.usernameBox = DirectEntry(text="", pos=p, scale=.04, initialText=self.username, numLines=1)
        # Username textbox where you type in your username

        p = boxloc + Vec3(-0.22, 0.0, 0.0)
        self.serverText = OnscreenText(text="Server:", pos=p, scale=0.05, bg=(0, 0, 0, 1), fg=(1, 1, 1, 1),
                                       align=TextNode.ARight)
        # "Server: " text that appears beside the server box

        p = boxloc + Vec3(-0.2, 0.0, 0.0)
        self.serverBox = DirectEntry(text="", pos=p, scale=.04, initialText=self.server, numLines=1)
        # server textbox where you type in the server

        p = boxloc + Vec3(0, 0, -0.090)
        self.loginButton = DirectButton(text="Login", pos=p, scale=0.048, relief=DGG.GROOVE,
                                        command=self.attemptConnect)
        # The 'Quit' button that will trigger the Quit function
        # when clicked

        p = boxloc + Vec3(1.20, 0, -0.9)
        self.quitButton = DirectButton(text="Quit", pos=p, scale=0.048, relief=DGG.GROOVE, command=self.showbase.quit)
        # The 'Quit' button that will trigger the Quit function
        # when clicked

        p = boxloc + Vec3(0, -0.4, 0)
        self.statusText = OnscreenText(text=statusText, pos=p, scale=0.043, fg=(1, 0.5, 0, 1), align=TextNode.ACenter)

    # A simple text object that you can display an error/status messages
    # to the user
    def updateStatus(self, statusText):
        self.statusText.setText(statusText)

    # all this does is change the status text.

    def checkBoxes(self):
        # checks to make sure the user inputed a username and server:
        #       if they didn't it will spit out an error message
        self.updateStatus("")
        if self.usernameBox.get() == "":
            if self.serverBox.get() == "":
                self.updateStatus("You must enter a username and server before connecting.")
            else:
                self.updateStatus("You must specify a username")
                self.serverBox['focus'] = 0
                self.usernameBox['focus'] = 1
            return False
        elif self.serverBox.get() == "":
            self.updateStatus("You must enter a server")
            self.usernameBox['focus'] = 0
            self.serverBox['focus'] = 1
            return False
        # if both boxes are filled then return True
        return True

    def attemptConnect(self):
        if self.checkBoxes():
            self.updateStatus("Attempting to connect...")
            self.joinServer(self.serverBox.get(), self.usernameBox.get())

    def joinServer(self, serverIp, username):
        self.ip = serverIp
        self.showbase.username = username
        self.updateStatus('Attempting to join server: ' + serverIp)
        # attempt to connect to the game server
        self.showbase.client = Client(self.ip, 9099, compress=True)
        if self.showbase.client.connected:
            print 'Connected to server, Awaiting authentication...'
            self.showbase.client.sendData(('username', self.showbase.username))
            self.showbase.taskMgr.add(self.authorizationListener, 'Authorization Listener')
        else:
            self.updateStatus('Could not Connect...')

    def authorizationListener(self, task):
        temp = self.showbase.client.getData()
        auth = False
        if temp:
            for package in temp:
                if len(package) == 2:
                    if package[0] == 'auth':
                        print 'Authentication Successful'
                        auth = True
                    elif package[0] == 'fail':
                        self.updateStatus('Username already taken...')
                        return task.done
                    else:
                        self.showbase.client.passData(package)
        if auth:
            self.showbase.goToLobby()
            return task.done
        return task.again

    def cycleLoginBox(self):
        # function is triggered by the tab key so you can cycle between
        # the two input fields like on most login screens
        if self.serverBox['focus'] == 1:
            self.serverBox['focus'] = 0
            self.usernameBox['focus'] = 1
        elif self.usernameBox['focus'] == 1:
            self.usernameBox['focus'] = 0
            self.serverBox['focus'] = 1
            # IMPORTANT: When you change the focus to one of the text boxes,
            # you have to unset the focus on the other textbox.  If you do not
            # do this Panda seems to get confused.
