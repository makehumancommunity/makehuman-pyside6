"""
binary file operations on object3d
"""

import numpy as np
import os

def exportObj3dBinary(filename, path, obj):

    content = {}

    # binary structure
    # first header

    lname = len(obj.name)
    header_type = np.dtype({'names':('objname', 'numverts', 'prnt', 'fcnt', 'ucnt'), 'formats':('|S'+str(lname), 'i4', 'i4', 'i4', 'i4')})
    content["header"] = np.array([(obj.name, obj.n_origverts, obj.prim, obj.n_faces, obj.n_fuvs)], dtype=header_type)

    # then all names of the groups
    #
    content["grpNames"] = obj.npGrpNames

    # the xyz coordinates of vertices
    # then uv-coordinates
    #
    content["coord"] = obj.coord
    content["uvs"] = obj.uvs

    # now the overflowbuffer to help OpenGL
    #
    content["overflow"] = obj.overflow 
    ngroups = len(obj.npGrpNames)

    # now the more complex calculation of the faces as
    # index-buffer groups (i4) Element-Start, (i4) NumFaces, and a bool)
    #
    groupinfo = np.zeros(ngroups, dtype=np.dtype('i4,i4,?'))
    allvertnums = 0
    allfaces = 0
    for num, npelem in enumerate (obj.npGrpNames):
        cnt = 0
        elem = npelem.decode("utf-8")
        group = obj.loadedgroups[elem]
        faces = group["v"]
        lfaces = len(faces)
        for face in faces:
            cnt += len(face)
        groupinfo[num] = tuple([allvertnums, lfaces, group["uv"]])
        allvertnums += cnt
        allfaces += lfaces
    
    # relative positions where the faces start
    # and flat array for the vertnumbers itself
    #
    facestart = np.zeros(allfaces, dtype=np.dtype('i4'))
    faceverts = np.zeros(allvertnums, dtype=np.dtype('i4'))
    finfocnt = 0
    fvertcnt = 0
    for num, npelem in enumerate (obj.npGrpNames):
        pos = 0
        elem = npelem.decode("utf-8")
        group = obj.loadedgroups[elem]
        faces = group["v"]
        for face in faces:
            facestart[finfocnt] = pos
            for vert in face:
                faceverts[fvertcnt] = vert
                fvertcnt += 1
            pos += len(face)
            finfocnt += 1

    content["groupinfo"] = groupinfo
    content["facestart"] = facestart
    content["faceverts"] = faceverts

    if filename.endswith(".obj"):
        filename = filename[:-3] + "npz"
    else:
        filename += ".npz"
 
    outfile = os.path.join(path, filename)
    obj.env.logLine(8, "Save compressed: " + outfile)
    f = open(outfile, "wb")
    np.savez_compressed(f, **content)
    f.close()


