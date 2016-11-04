from direct.gui.DirectGui import DGG, DirectFrame, DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Vec3, TextNode

from gamedata import GameData
from user import User


class Lobby(DirectObject):
    def __init__(self, main):
        DirectObject.__init__(self)

        self.showbase = main

        self.status = OnscreenText(text="", pos=Vec3(0, -0.35, 0), scale=0.05, fg=(1, 0, 0, 1), align=TextNode.ACenter,
                                   mayChange=True)

        self.background = DirectFrame(
            frameSize=(-1, 1, -1, 1),
            frameTexture='media/gui/mainmenu/menu.png',
            parent=self.showbase.render2d,
        )

        self.title = OnscreenText(
            text='Main Menu',
            fg=(1, 1, 1, 1),
            parent=self.background,
            pos=(-0.6, 0.1),
            scale=0.06
        )

        self.buttons = []
        controlButtons = Vec3(-0.60, 0, -0.79)
        # Toggle ready
        p = controlButtons + Vec3(-0.25, 0, 0)
        self.toggleReadyButton = DirectButton(
            text='Ready/Unready',
            pos=p,
            scale=0.048,
            relief=DGG.GROOVE,
            command=self.toggleReady,
        )

        self.ready = False

        self.showbase.users = []

    def updateLobby(self, task):
        temp = self.showbase.client.getData()
        for package in temp:
            if len(package) == 2:
                print 'Received: ', str(package)
                if package[0] == 'reset':
                    self.showbase.users = []
                    print 'cleared users'
                elif package[0] == 'client':
                    self.showbase.users.append(User(package[1]))
                    for user in self.showbase.users:
                        print user.name, user.ready
                    print 'all users'
                elif package[0] == 'ready':
                    for user in self.showbase.users:
                        if user.name == package[1][0]:
                            user.ready = package[1][1]
                    for user in self.showbase.users:
                        print user.name, user.ready
                    print 'all users'
                elif package[0] == 'disconnect':
                    for user in self.showbase.users:
                        if user.name == package[1]:
                            self.showbase.users.remove(user)
                    for user in self.showbase.users:
                        print user.name, user.ready
                    print 'all users'
                elif package[0] == 'gamedata':
                    self.showbase.gameData = GameData()
                    self.showbase.gameData.unpackageData(package[1])
                elif package[0] == 'state':
                    print 'state: ', package[1]
                    if package[1] == 'preround':
                        self.showbase.startRound()
                        return task.done
        return task.again

    def toggleReady(self):
        self.ready = not self.ready
        self.showbase.client.sendData(('ready', self.ready))

    def hide(self):
        self.background.hide()
        for b in self.buttons:
            b.hide()
        self.status.hide()
        self.toggleReadyButton.hide()

        self.showbase.taskMgr.remove('Update Lobby')

    def show(self):
        self.background.show()
        for b in self.buttons:
            b.show()
        self.status.show()
        self.toggleReadyButton.show()

        # Add the game loop procedure to the task manager.
        self.showbase.taskMgr.add(self.updateLobby, 'Update Lobby')
