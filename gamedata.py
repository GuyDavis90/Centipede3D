from random import random


# TODO: Revisit parent class
class GameData(object):
    def __init__(self, isServer=False):
        self.randSeed = 0.0
        self.maxFoods = 32

        if isServer:
            self.randSeed = random()

    def packageData(self):
        data = []
        data.append(('seed', self.randSeed))
        return data

    def unpackageData(self, data):
        for package in data:
            if package[0] == 'seed':
                self.randSeed = package[1]
