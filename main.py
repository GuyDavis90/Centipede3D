import sys

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData

from start import Start
from lobby import Lobby
from round import Round

loadPrcFileData(
    "",
    """
    window-title CENTIPEDE!
    fullscreen 0
    win-size 960 540 #1280 720
    cursor-hidden 0
    sync-video 1
    frame-rate-meter-update-interval 0.5
    show-frame-rate-meter 1
    """
)


class Main(ShowBase):
    start = None
    lobby = None
    round = None

    def __init__(self):
        ShowBase.__init__(self)

        self.start = Start(self)

    def goToLobby(self):
        self.start.cleanup()
        self.start = None
        self.lobby = Lobby(self)
        self.lobby.show()

    def startRound(self):
        self.lobby.hide()
        self.round = Round(self)

    def endRound(self):
        self.round.destroy()
        del self.round
        self.round = None
        self.lobby.show()

    def quit(self):
        sys.exit()


game = Main()
game.run()
