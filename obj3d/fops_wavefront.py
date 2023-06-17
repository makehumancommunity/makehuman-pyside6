"""
file operations, wavefront OBJ
"""

def importWaveFront(path, obj):
    """
    f  = face
    g  = groups are used to add faces to
    o  = object (name), only one is used
    v  = positions (3d)
    vt = positions (texture)
    usemtl = material (skipped)
    """

    print ("load " + path)
    try:
        f = open(path, 'r', encoding="utf-8")
    except IOError:
        return (False, "Cannot open file " + path)
    else:

        verts  = []
        uvs    = []
        groups = {}
        groupnames = [] # to keep the group order
        objname = None
        prim = 0        # verts per face (either 3 or 4)
        ln = 0          # line number
        fcnt = 0        # face-counter
        ucnt = 0        # UV-face counter

        groupnames.append("mh_default")
        g = groups["mh_default"] = {"v": [], "uv": [] }


        for line in f:
            ln += 1
            words = line.split()

            lwords = len(words) -1
            if lwords <= 0:
                continue

            command = words[0]

            # v and vt simply fill buffers
            #
            if command == 'v':
                verts.append((float(words[1]), float(words[2]), float(words[3])))

            elif command == 'vt':
                uvs.append((float(words[1]), float(words[2])))

            # f, faces, this data is stored groupwise, index counts from 1
            # a/b ... first one is vertex-index, second one UV
            #
            elif command == 'f':
                vInd  = []
                uvInd = []

                if lwords != 3 and lwords != 4:
                    f.close()
                    return (False, "File " + path + " line: " + str(ln) + " => Vertex per face must be either 3 or 4")
                if prim != 0 and prim != lwords:
                    f.close()
                    return (False, "File " + path + " line: " + str(ln) + " => Vertex per face must not mix")

                prim = lwords
                for elem in words[1:]:
                    columns = elem.split('/')
                    vInd.append(int(columns[0]) - 1)

                    if len(columns) > 1 and columns[1] != '':
                        uvInd.append(int(columns[1]) - 1)

                g["v"].append(vInd)
                fcnt += 1

                if len(uvInd) > 0:
                    g["uv"].append(uvInd)
                    ucnt += 1

            elif command == 'g':
                gname = words[1]
                if gname not in groups:
                    g = groups[gname] = {"v": [], "uv": [] }
                    groupnames.append(gname)

            elif command == 'o':
                objname = words[1]

            else:
                # print ("Ignore: " + line)
                pass
        f.close()

    # delete empty groups
    # must be done in two steps not to destroy iteration, first step can delete empty uvs
    #
    delete = []
    for g in groups:
        if len(groups[g]["v"]) == 0:
            delete.append(g)
            groupnames.remove(g)
        if len(groups[g]["uv"]) == 0:
            del groups[g]["uv"]

    for d in delete:
        del groups[d]

    # sanity test for finding vertices costs too much time
    #
    # TODO for tri mesh generate 4 vertex in vInd ? (at this place?)
    #
    obj.setName(objname)
    obj.setGroupNames(groupnames)
    obj.createGLVertPos(verts)          # TODO consider to recombine createGLVertPos and createGLFaces
    obj.createGLFaces(fcnt, ucnt, prim, groups)

    return (True, None)
