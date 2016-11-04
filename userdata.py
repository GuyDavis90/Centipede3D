class UserData(object):
    def __init__(self, thisPlayer=False):
        self.thisPlayer = thisPlayer
        self.newDest = False
        self.centipede = None

    def makeUpdatePackets(self):
        packets = []
        # new destination
        if self.newDest:
            packets.append(('updateDest', self.centipede.getDestinationUpdate()))
            self.newDest = False
        return packets

    def processUpdatePacket(self, packet):
        if len(packet) == 2:
            if packet[0] == 'updateDest':
                self.centipede.setDestination(packet[1])
                self.newDest = True
