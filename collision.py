from panda3d.core import CollisionSphere, CollisionNode
from direct.actor.Actor import BitMask32


def initCollisionSphere(obj, desc, radiusMultiplier, intoMask=BitMask32(0x1), isFromCollider=False):
    # Get the size of the object for the collision sphere.
    bounds = obj.getChild(0).getBounds()
    center = bounds.getCenter()
    radius = bounds.getRadius() * radiusMultiplier

    # Create a collision sphere and name it something understandable.
    collSphereStr = desc
    cNode = CollisionNode(collSphereStr)
    cNode.addSolid(CollisionSphere(center, radius))
    if not isFromCollider:
        cNode.setFromCollideMask(BitMask32(0x0))
    cNode.setIntoCollideMask(intoMask)

    cNodepath = obj.attachNewNode(cNode)
    # if show:
    #cNodepath.show()

    # Return a tuple with the collision node and its corrsponding string so
    # that the bitmask can be set.
    return cNodepath, collSphereStr
