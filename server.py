from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import NetDatagram
from panda3d.core import PointerToConnection, NetAddress
from panda3d.core import QueuedConnectionManager, QueuedConnectionListener
from panda3d.core import QueuedConnectionReader, ConnectionWriter

import rencode


class Server(DirectObject):
    # TODO: Perhaps a better way to do this?
    handleNewConnection = None
    handleLostConnection = None

    def __init__(self, port, backlog=1000, compress=False):
        DirectObject.__init__(self)

        self.port = port
        self.compress = compress

        self.cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(self.cManager, 0)
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        self.cWriter = ConnectionWriter(self.cManager, 0)

        self.passedData = []

        self.connect(port, backlog)
        self.startPolling()

    def connect(self, port, backlog):
        # Bind to our socket
        tcpSocket = self.cManager.openTCPServerRendezvous(port, backlog)
        self.cListener.addConnection(tcpSocket)

    def startPolling(self):
        self.addTask(self.tskListenerPolling, "serverListenTask", -40)
        self.addTask(self.tskDisconnectPolling, "serverDisconnectTask", -39)

    def tskListenerPolling(self, task):
        if self.cListener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()

            if self.cListener.getNewConnection(rendezvous, netAddress, newConnection):
                newConnection = newConnection.p()
                newConnection.setNoDelay(True)
                newConnection.setKeepAlive(True)
                if self.handleNewConnection:
                    self.handleNewConnection(newConnection)
                self.cReader.addConnection(newConnection)  # Begin reading connection
        return Task.cont

    def tskDisconnectPolling(self, task):
        while self.cManager.resetConnectionAvailable():
            connPointer = PointerToConnection()
            self.cManager.getResetConnection(connPointer)
            connection = connPointer.p()

            # Remove the connection we just found to be "reset" or "disconnected"
            self.cReader.removeConnection(connection)

            if self.handleLostConnection:
                self.handleLostConnection(connection)

        return Task.cont

    def processData(self, netDatagram):
        myIterator = PyDatagramIterator(netDatagram)
        return self.decode(myIterator.getString())

    def encode(self, data, compress=False):
        # encode(and possibly compress) the data with rencode
        return rencode.dumps(data, compress)

    def decode(self, data):
        # decode(and possibly decompress) the data with rencode
        return rencode.loads(data)

    def sendData(self, data, con):
        myPyDatagram = PyDatagram()
        myPyDatagram.addString(self.encode(data, self.compress))
        self.cWriter.send(myPyDatagram, con)

    def passData(self, data, connection):
        self.passedData.append((data, connection))

    def getData(self):
        data = self.passedData
        self.passedData = []
        while self.cReader.dataAvailable():
            datagram = NetDatagram()
            if self.cReader.getData(datagram):
                data.append((datagram.getConnection(), self.processData(datagram)))
        return data
