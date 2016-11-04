# TODO: User class for client and subclassed for server?
class User(object):
    def __init__(self, name, connection=None):
        self.name = name
        self.connection = connection
        self.ready = False
        self.sync = False
