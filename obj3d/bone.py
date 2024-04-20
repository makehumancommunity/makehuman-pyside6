
import numpy as np

class cBone():
    def __init__(self, skel, name, parent, head, tail, roll=0, reference=None, weights=None):
        """
        headPos and tailPos should be in world space coordinates (relative to root).
        parentName should be None for a root bone.
        """
        self.name = name
        self.skeleton = skel

        self.head = head
        self.tail = tail

        self.headPos = np.zeros(3,dtype=np.float32)
        self.tailPos = np.zeros(3,dtype=np.float32)

