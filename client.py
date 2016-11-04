from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import ConnectionWriter
from panda3d.core import NetDatagram
from panda3d.core import PointerToConnection
from panda3d.core import QueuedConnectionManager
from panda3d.core import QueuedConnectionReader

import rencode


class Client(DirectObject):
    def __init__(self, host, port, timeout=3000, compress=False, connectionStateChangedHandler=None):
        DirectObject.__init__(self)

        self.connectionStateChangedHandler = connectionStateChangedHandler

        self.myConnection = None

        self.host = host
        self.port = port
        self.timeout = timeout
        self.compress = compress

        self.cManager = QueuedConnectionManager()
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        self.cWriter = ConnectionWriter(self.cManager, 0)

        # By default, we are not connected
        self.connected = False

        self.passedData = []

        self.connect(self.host, self.port, self.timeout)

    def cleanup(self):
        self.removeAllTasks()

    def startPolling(self):
        self.doMethodLater(0.1, self.tskDisconnectPolling, "clientDisconnectTask")

    def connect(self, host, port, timeout=3000):
        # Connect to our host's socket
        self.myConnection = self.cManager.openTCPClientConnection(host, port, timeout)
        if self.myConnection:
            self.myConnection.setNoDelay(True)
            self.myConnection.setKeepAlive(True)
            print "Connected"
            self.cReader.addConnection(self.myConnection)  # receive messages from server
            self.connected = True  # Let us know that we're connected
            self.startPolling()
            if self.connectionStateChangedHandler:
                self.connectionStateChangedHandler.handleConnection()
        else:
            print "Unable to connect"
            if self.connectionStateChangedHandler:
                self.connectionStateChangedHandler.handleFailure()

    def tskDisconnectPolling(self, task):
        if not self.connected:
            return Task.done

        # TODO: Hacky sending nothing to force disconnect triggers
        #self.sendData()
        # Also checking for dataAvailable on reader will trigger the connection disconnected
        self.cReader.dataAvailable()
        # TODO: Confirm this works for client side (to both game server and master server)
        while self.cManager.resetConnectionAvailable():
            connPointer = PointerToConnection()
            self.cManager.getResetConnection(connPointer)
            connection = connPointer.p()

            # Remove the connection we just found to be "reset" or "disconnected"
            self.cReader.removeConnection(connection)

            # Let us know that we are not connected
            self.connected = False
            print "disconnected"

            if self.connectionStateChangedHandler:
                self.connectionStateChangedHandler.handleDisconnection()

        return Task.again

    def processData(self, netDatagram):
        myIterator = PyDatagramIterator(netDatagram)
        return self.decode(myIterator.getString())

    def encode(self, data, compress=False):
        # encode(and possibly compress) the data with rencode
        return rencode.dumps(data, compress)

    def decode(self, data):
        # decode(and possibly decompress) the data with rencode
        return rencode.loads(data)

    def sendData(self, data=None):
        myPyDatagram = PyDatagram()
        myPyDatagram.addString(self.encode(data, self.compress))
        self.cWriter.send(myPyDatagram, self.myConnection)

    def passData(self, data):
        self.passedData.append(data)

    def getData(self):
        data = self.passedData
        self.passedData = []
        while self.cReader.dataAvailable():
            datagram = NetDatagram()
            if self.cReader.getData(datagram):
                data.append(self.processData(datagram))
        return data
