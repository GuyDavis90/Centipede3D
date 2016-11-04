# World Class
# TODO: Revisit parent class
class World(object):
    def __init__(self, showbase):
        # Load the environment model (Ground and Surrounding Rocks)
        self.ground = showbase.loader.loadModel('models/arena')
        # Reparent the model to render
        self.ground.reparentTo(showbase.render)

    def destroy(self):
        self.ground.detachNode()
        self.ground = None
