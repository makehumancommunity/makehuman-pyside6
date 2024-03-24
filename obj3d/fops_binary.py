"""
binary file operations on object3d
"""

import numpy as np
import os
from obj3d.fops_wavefront import importWaveFront

def exportObj3dBinary(filename, path, obj, content = {}):

    #content = {}

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
    vertsperface = np.zeros(allfaces, dtype=np.dtype('i4'))
    faceverts = np.zeros(allvertnums, dtype=np.dtype('i4'))
    finfocnt = 0
    fvertcnt = 0
    for num, npelem in enumerate (obj.npGrpNames):
        pos = 0
        elem = npelem.decode("utf-8")
        group = obj.loadedgroups[elem]
        faces = group["v"]
        for face in faces:
            for vert in face:
                faceverts[fvertcnt] = vert
                fvertcnt += 1
            vertsperface[finfocnt] = len(face)
            pos += len(face)
            finfocnt += 1

    content["groupinfo"] = groupinfo
    content["vertsperface"] = vertsperface
    content["faceverts"] = faceverts

    if filename.endswith(".obj"):
        filename = filename[:-3] + "npz"
    else:
        filename += ".npz"

    # check if npzip directory exists, if not create it
    # if not possible no zip file + message
    #
    outdir = os.path.join(path, "npzip")
    if not os.path.isdir(outdir):
        print ("Need to create " + outdir)
        obj.env.logLine(8, "Create directory: " + outdir)
        outerr = None
        try:
            os.mkdir(outdir)
        except OSError as error:
            return (False, str(error))

    outfile = os.path.join(outdir, filename)
    obj.env.logLine(8, "Save compressed: " + outfile)
    try:
        f = open(outfile, "wb")
        np.savez_compressed(f, **content)
    except OSError as error:
        return (False, str(error))
    finally:
        f.close()

    return(True, None)


def importObj3dBinary(path, obj):
    print ("read binary " + path)
    npzfile = np.load(path)
    for elem in ['header', 'grpNames', 'coord', 'uvs', 'overflow', 'groupinfo', 'vertsperface', 'faceverts']:
        if elem not in npzfile:
            error =  "Malformed file, missing component " + elem
            return (False, error)

    # now get data from binary, header
    #
    header = list(npzfile['header'][0])
    obj.name        = header[0].decode("utf-8")
    (obj.n_origverts, prim, fcnt, ucnt) = header[1:]

    # next stuff is identical to npz file, number of elements is mostly added
    #
    obj.npGrpNames = npzfile['grpNames']
    obj.n_groups = len(obj.npGrpNames)

    # xyz coordinates of vertices, uvs and OpenGL overflow buffer
    #
    obj.coord    = npzfile["coord"]
    obj.n_verts = len(obj.coord)
    obj.uvs      = npzfile["uvs"]
    obj.n_uvs   = len(obj.uvs)
    obj.overflow = npzfile["overflow"]

    # regenerate groups from groupinfo, vertsperface, faceverts
    # index-buffer groups (Start, NumFaces, bool)
    #
    verts = npzfile["faceverts"]
    fsize = npzfile["vertsperface"]
    groups = {}
    j = 0
    for num, elem in enumerate(npzfile["groupinfo"]):
        start = elem[0]
        faces = elem[1]
        f = []
        fs = start
        for i in range(faces):
            v = []
            for k in range(0, fsize[j]):
                v.append(verts[fs+k])
            f.append(v)
            fs += fsize[j]
            j += 1

        group =  obj.npGrpNames[num].decode("utf-8")
        groups[group] = { "v": f, "uv": elem[2] }

    obj.createGLFaces(fcnt, ucnt, prim, groups)

    return (True, None)

def importObjFromFile(path, obj):
    """
    check if binary file exists, directory in inside subdirectory named npzip
    """
    if obj.name_loaded.endswith(".obj"):
        binfile = os.path.join(obj.dir_loaded, "npzip", obj.name_loaded[:-3] + "npz")
        if os.path.isfile(binfile):
            return(importObj3dBinary(binfile, obj))

    # only ASCII
    #
    obj.env.logLine(8, "Load: " + path)
    return(importWaveFront(path, obj))


def exportAssetBinary(filename, path, asset):
    content = {}

    # binary structure
    # first header
    mtags = "|".join(asset.tags)
    ltags = "|S" + str(len(mtags))

    lname = "|S" + str(len(asset.name))
    llics = "|S" + str(len(asset.license))
    luuid = "|S" + str(len(asset.uuid))
    lauth = "|S" + str(len(asset.author))
    ldesc = "|S" + str(len(asset.description))
    lmesh = "|S" + str(len(asset.meshtype))

    nrefverts = 3 if asset.weights[:,1:].any() else 1

    asset_type = np.dtype({'names':('name', 'uuid', 'author', 'description', 'meshtype', 'refverts', 'version', 'zdepth', 'license', 'tags'),
        'formats':(lname, luuid, lauth, ldesc, lmesh, 'i4', 'i4', 'i4', llics, ltags)})
    content["asset"] = np.array([(asset.name, asset.uuid, asset.author, asset.description, asset.meshtype, nrefverts, asset.version,
        asset.z_depth, asset.license, mtags)], dtype=asset_type)

    lmat = "|S" + str(len(asset.material))
    if asset.vertexboneweights_file is None:
        vwfile = ""
    else:
        vwfile = asset.vertexboneweights_file
    lweight = "|S" + str(len(vwfile))

    files_type = np.dtype({'names':('material', 'weight'), 'formats': (lmat, lweight)})
    content["files"] =  np.array([(asset.material_orgpath, vwfile)], dtype=files_type)

    if nrefverts == 3:
        content["ref_vIdxs"] = asset.ref_vIdxs
        content["offsets"] = asset.offsets
        content["weights"] = asset.weights
    else:
        content["ref_vIdxs"] = asset.ref_vIdxs[:,0]
        content["weights"] = asset.weights[:,0]

    if np.any(asset.deleteVerts):
        content["deleteVerts"] = asset.deleteVerts

    exportObj3dBinary(filename, path, asset.obj, content)

