from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData

from game import Game
from gamedata import GameData
from server import Server
from user import User
from userdata import UserData

loadPrcFileData(
    "",
    """
        sync-video 1
        frame-rate-meter-update-interval 0.5
        show-frame-rate-meter 1
        #window-type none
    """
)

gameTick = 1.0 / 30.0


class GameServer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.server = Server(9099, compress=True)
        self.server.handleNewConnection = self.handleNewConnection
        self.server.handleLostConnection = self.handleLostConnection

        self.tempConnections = []
        self.currentPlayers = []

        self.taskMgr.doMethodLater(0.5, self.lobbyLoop, 'Lobby Loop')

    def broadcastData(self, data):
        # Broadcast data out to all users
        for user in self.currentPlayers:
            if user.connection:
                self.server.sendData(data, user.connection)

    def getUsers(self):
        # return a list of all users
        return self.currentPlayers

    def getData(self):
        data = []
        for datagram in self.server.getData():
            connection = datagram[0]
            package = datagram[1]
            if package is None:
                continue
            if connection in self.tempConnections:
                self.processTempConnection(datagram)
                continue
            for authed in self.currentPlayers:
                if connection == authed.connection:
                    data.append((package, connection))
        return data

    def handleNewConnection(self, connection):
        print "handleNewConnection"
        self.tempConnections.append(connection)

    def handleLostConnection(self, connection):
        print "handleLostConnection"
        # remove from our activeConnections list
        if connection in self.tempConnections:
            self.tempConnections.remove(connection)
        for user in self.currentPlayers:
            if connection == user.connection:
                user.connection = None
                self.server.passData(('disconnect', user.name), None)

    def processTempConnection(self, datagram):
        connection = datagram[0]
        package = datagram[1]
        if len(package) == 2:
            if package[0] == 'username':
                print 'attempting to authenticate', package[1]
                self.tempConnections.remove(connection)

                user = User(package[1], connection)
                # confirm authorization
                self.server.sendData(('auth', user.name), user.connection)
                self.updateClient(user)
                self.currentPlayers.append(user)

    def updateClient(self, user):
        for existing in self.currentPlayers:
            if existing.name != user.name:
                self.server.sendData(('client', existing.name), user.connection)
                self.server.sendData(('ready', (existing.name, existing.ready)), user.connection)
                if existing.connection:
                    self.server.sendData(('client', user.name), existing.connection)
        self.server.sendData(('client', user.name), user.connection)

    def returnToLobby(self):
        self.taskMgr.doMethodLater(0.5, self.cleanupAndStartLobby, 'Return To Lobby')

    def cleanupAndStartLobby(self, task):
        self.cleanupGame()

        for currentPlayer in self.currentPlayers:
            self.server.sendData(('reset', 'bloop'), currentPlayer.connection)
            for existing in self.currentPlayers:
                self.server.sendData(('client', existing.name), currentPlayer.connection)
                self.server.sendData(('ready', (existing.name, existing.ready)), currentPlayer.connection)

        self.taskMgr.doMethodLater(0.5, self.lobbyLoop, 'Lobby Loop')

        return task.done

    def lobbyLoop(self, task):
        temp = self.getData()
        for package in temp:
            if len(package) == 2:
                packet = package[0]
                connection = package[1]

                print "Received: ", str(package)
                if len(packet) == 2:
                    # check to make sure connection has username
                    for user in self.currentPlayers:
                        if user.connection == connection:
                            # if chat packet
                            if packet[0] == 'chat':
                                print 'Chat: ', packet[1]
                                # Broadcast data to all clients ("username: message")
                                self.broadcastData(('chat', (user.name, packet[1])))
                            # else if ready packet
                            elif packet[0] == 'ready':
                                print user.name, ' changed readyness!'
                                user.ready = packet[1]
                                self.broadcastData(('ready', (user.name, user.ready)))
                            # else if disconnect packet
                            elif packet[0] == 'disconnect':
                                print user.name, ' is disconnecting!'
                                self.currentPlayers.remove(user)
                                self.broadcastData(('disconnect', user.name))
                            # break out of for loop
                            break
        # if all players are ready and there is X of them
        gameReady = True
        # if there is any clients connected
        if not self.getUsers():
            gameReady = False
        for user in self.currentPlayers:
            if not user.ready:
                gameReady = False
        if gameReady:
            self.prepareGame()
            return task.done
        return task.again

    def prepareGame(self):
        if self.camera:
            # Disable Mouse Control for camera
            self.disableMouse()

            self.camera.setPos(0, 0, 500)
            self.camera.lookAt(0, 0, 0)

        self.gameData = GameData(True)

        # game data
        self.broadcastData(('gamedata', self.gameData.packageData()))
        self.broadcastData(('state', 'preround'))
        print "Preparing Game"
        self.gameTime = 0
        self.tick = 0

        usersData = []
        for user in self.currentPlayers:
            user.gameData = UserData()
            usersData.append(user.gameData)
        print usersData
        self.game = Game(self, usersData, self.gameData)
        self.taskMgr.doMethodLater(0.5, self.roundReadyLoop, 'Game Loop')
        print "Round ready State"

    def cleanupGame(self):
        self.game.destroy()
        self.game = None

    def roundReadyLoop(self, task):
        temp = self.getData()
        for package in temp:
            if len(package) == 2:
                print "Received: ", str(package)
                if len(package[0]) == 2:
                    for user in self.currentPlayers:
                        if user.connection == package[1]:
                            if package[0][0] == 'round':
                                if package[0][1] == 'sync':
                                    user.sync = True
        # if all players are ready and there is X of them
        roundReady = True
        # if there is any clients connected
        for user in self.currentPlayers:
            if not user.sync:
                roundReady = False
        if roundReady:
            self.taskMgr.doMethodLater(2.5, self.gameLoop, 'Game Loop')
            print "Game State"
            return task.done
        return task.again

    def gameLoop(self, task):
        # process incoming packages
        temp = self.getData()
        for package in temp:
            if len(package) == 2:
                # check to make sure connection has username
                for user in self.currentPlayers:
                    if user.connection == package[1]:
                        try:
                            user.gameData.processUpdatePacket(package[0])
                        except AttributeError:
                            print "Player must have joined mid game! :O"

        # get frame delta time
        dt = self.taskMgr.globalClock.getDt()
        self.gameTime += dt
        # if time is less than 3 secs (countdown for determining pings of clients?)
        # tick out for clients
        while self.gameTime > gameTick:
            # update all clients with new info before saying tick
            for user in self.currentPlayers:
                try:
                    updates = user.gameData.makeUpdatePackets()
                    for packet in updates:
                        self.broadcastData((user.name, packet))
                except AttributeError:
                    print "Player must have joined mid game! :O"
            self.broadcastData(('tick', self.tick))
            self.gameTime -= gameTick
            self.tick += 1
            # run simulation
            if not self.game.runTick(gameTick, self.tick):
                print 'Game Over'
                self.broadcastData(("game", "over"))
                # send to all players that game is over (they know already but whatever)
                # and send final game data/scores/etc
                for user in self.currentPlayers:
                    user.ready = False
                self.returnToLobby()
                return task.done
        return task.cont


gameServer = GameServer()
gameServer.run()
