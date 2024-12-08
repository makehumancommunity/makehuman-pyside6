"""
bvh exporter
"""
import os
import numpy as np
from obj3d.animation import BVH

class bvhExport:
    def __init__(self, glob, onground=False, scale =0.1):

        self.glob = glob
        self.env = glob.env
        self.onground = onground
        self.scale = scale
        self.lowestPos = 0.0

        self.bvh = BVH(glob, "export")
        self.skeldef = []
    
    def calcJoints(self, bones):
        for name, bone in bones.items():
            if bone.parent is None:
                joint = self.bvh.addJoint(name, None)
                joint.offset = bone.headPos
                joint.channels = ["Xposition", "Yposition", "Zposition", "Xrotation", "Yrotation", "Zrotation"]
            else:
                joint = self.bvh.addJoint(name, self.bvh.joints[bone.parent.name])
                joint.offset = bone.headPos - bone.parent.headPos
                joint.channels = ["Xrotation", "Yrotation", "Zrotation"]
            if len(bone.children) == 0:
                joint = self.bvh.addJoint("", self.bvh.joints[name])
                joint.offset = bone.tailPos - bone.headPos


    def writeJoint(self, joint, l):
        name = joint.name
        l1 = l+1
        offset = joint.offset
        if name == "":
            self.skeldef.append("\t" * l1 + "End Site\n" + "\t" * l1 + "{\n")
            self.skeldef.append("\t" * (l1+1) + "OFFSET %f %f %f\n" % (offset[0], offset[1], offset[2]) + "\t" * l1 + "}\n")
            return

        if joint.parent is None:
            # root bone
            #
            self.skeldef.append("ROOT " + name + "\n{\n")
        else:
            self.skeldef.append("\t" * l + "JOINT " + name + "\n" + "\t" * l + "{\n")

        self.skeldef.append("\t" * l1 + "OFFSET %f %f %f\n" % (offset[0], offset[1], offset[2]))
        self.skeldef.append("\t" * l1 + 'CHANNELS %s %s\n' % (len(joint.channels), " ".join(joint.channels)))

        for b in joint.children:
            self.writeJoint(b, l1)
        self.skeldef.append("\t" * l + "}\n")

    def ascSave(self, baseclass, filename):

        if baseclass.skeleton is None:
            self.env.last_error = "No skeleton selected"
            return False

        if baseclass.bvh is None:
            self.env.last_error = "No animation loaded"
            return False

        bones = baseclass.skeleton.bones
        self.calcJoints(bones)

        header ="HIERARCHY\n"
        self.writeJoint(self.bvh.bvhJointOrder[0], 0)

        frameheader = "MOTION\nFrames: %s\nFrame Time: %f\n" % (baseclass.bvh.frameCount, baseclass.bvh.frameTime)

        try:
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(header)
                for line in self.skeldef:
                    f.write(line)
                f.write(frameheader)

        except IOError as error:
            self.env.last_error = str(error)
            return False

        return True
                               

