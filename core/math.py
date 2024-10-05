import math
import numpy as np

"""
quaternionToRotMatrix           Return homogeneous rotation matrix from quaternion.
quaternionFromMatrix            Return quaternion from rotation matrix.
quaternionMult                  Return multiplication of two quaternions.
quaternionSlerp                 Return spherical linear interpolation between two quaternions.
quaternionSlerpFromMatrix       do a slerp from Restmatix by ratio
"""

_EPS = np.finfo(float).eps * 4.0

def eulerMatrixXYZ(ri, rj, rk, i, j, k):
    M = np.identity(4)
    si, sj, sk = math.sin(ri), math.sin(rj), math.sin(rk)
    ci, cj, ck = math.cos(ri), math.cos(rj), math.cos(rk)
    cc, cs = ci*ck, ci*sk
    sc, ss = si*ck, si*sk

    M[i, i] = cj*ck
    M[i, j] = sj*sc-cs
    M[i, k] = sj*cc+ss
    M[j, i] = cj*sk
    M[j, j] = sj*ss+cc
    M[j, k] = sj*cs-sc
    M[k, i] = -sj
    M[k, j] = cj*si
    M[k, k] = cj*ci
    return(M)


def eulerMatrix(x, y, z, s="xyz"):
    if s == "xyz":
        return eulerMatrixXYZ(x, y, z, 0, 1, 2)
    elif s == "xzy":
        return eulerMatrixXYZ(-x, -y, -z, 0, 2, 1)
    elif s == "yzx":
        return eulerMatrixXYZ(x, y, z, 1, 2, 0)
    elif s == "yxz":
        return eulerMatrixXYZ(-x, -y, -z, 1, 0, 2)
    elif s == "zxy":
        return eulerMatrixXYZ(x, y, z, 2, 0, 1)
    # zyx
    return eulerMatrixXYZ(-x, -y, -z, 2, 1, 0)

def quaternionToRotMatrix(quaternion):
    """
    Return homogeneous rotation matrix from quaternion.
    TODO 3x3?
    """
    q = np.array(quaternion, dtype=np.float64, copy=True)
    n = np.dot(q, q)
    if n < _EPS:
        return np.identity(4)
    q *= math.sqrt(2.0 / n)
    q = np.outer(q, q)
    return np.array([
        [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
        [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
        [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
        [                0.0,                 0.0,                 0.0, 1.0]])

def quaternionFromMatrix(m):
    """
    Return quaternion from rotation matrix.
    """
    tr = m[0][0] + m[1][1] + m[2][2]

    if tr > 0:
        S = math.sqrt(tr+1.0) * 2 # S=4*qw
        qw = 0.25 * S
        qx = (m[2][1] - m[1][2]) / S
        qy = (m[0][2] - m[2][0]) / S
        qz = (m[1][0] - m[0][1]) / S
    elif (m[0][0] > m[1][1]) and (m[0][0] > m[2][2]):
        S = math.sqrt(1.0 + m[0][0] - m[1][1] -  m[2][2]) * 2 # S=4*qx
        qw = (m[2][1] - m[1][2]) / S
        qx = 0.25 * S;
        qy = (m[0][1] + m[1][0]) / S
        qz = (m[0][2] + m[2][0]) / S
    elif m[1][1] > m[2][2]:
        S = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2  # S=4*qy
        qw = (m[0][2] - m[2][0]) / S
        qx = (m[0][1] + m[1][0]) / S
        qy = 0.25 * S
        qz = (m[1][2] + m[2][1]) / S
    else:
        S = math.sqrt(1.0 +  m[2][2] - m[0][0] - m[1][1]) * 2 # S=4*qz
        qw = (m[1][0] - m[0][1]) / S
        qx = (m[0][2] + m[2][0]) / S
        qy = (m[1][2] + m[2][1]) / S
        qz = 0.25 * S

    return np.asarray([qw, qx, qy, qz], dtype=np.float32)

def quaternionMult(quaternion1, quaternion0):
    """
    Return multiplication of two quaternions.
    """
    w0, x0, y0, z0 = quaternion0
    w1, x1, y1, z1 = quaternion1
    return np.array([-x1*x0 - y1*y0 - z1*z0 + w1*w0,
                         x1*w0 + y1*z0 - z1*y0 + w1*x0,
                        -x1*z0 + y1*w0 + z1*x0 + w1*y0,
                         x1*y0 - y1*x0 + z1*w0 + w1*z0], dtype=np.float64)


def quaternionSlerp(quat0, quat1, fraction, shortestpath=True):
    """
    Return spherical linear interpolation between two quaternions.

    [quat0 * sin((1-fraction) * angle) + quat1 * sin(fraction*angle)] / sin(angle)

    the angle itself is the half angle between quat0 and quat1
    """
    q0 = np.array(quat0[:4], dtype=np.float64, copy=True)
    q1 = np.array(quat1[:4], dtype=np.float64, copy=True)

    # trivial cases
    #
    if fraction == 0.0:
        return q0
    elif fraction == 1.0:
        return q1

    # calculate dot-product => results in angle of cos(angle)
    #
    d = np.dot(q0, q1)
    if abs(abs(d) - 1.0) < _EPS:
        return q0

    if shortestpath and d < 0.0:
        # invert rotation
        d = -d
        np.negative(q1, q1)

    # now calculate angle
    #
    angle = math.acos(d)
    if abs(angle) < _EPS:
        return q0

    # distribute factors to get just one multiplication per matrix
    #
    isin = 1.0 / math.sin(angle)
    q0 *= math.sin((1.0 - fraction) * angle) * isin
    q1 *= math.sin(fraction * angle) * isin
    q0 += q1
    return q0


def quaternionSlerpFromMatrix(mat, fraction, shortestpath=True):
    """
    do a slerp from Restmatix
    """
    m = np.identity(4, dtype=np.float32)
    m[:3, :3] = mat
    quat0 = np.asarray([1,0,0,0], dtype=np.float32)
    quat1 = quaternionFromMatrix(m)
    return (quaternionSlerp(quat0, quat1, fraction, shortestpath))


def rotMatrix(angle, direction):
    sina = math.sin(angle)
    cosa = math.cos(angle)

    # convert direction to length of a unit vector
    #
    direction = np.array (direction[:3],  dtype=np.float32)
    direction /= math.sqrt(np.dot(direction, direction))

    R = np.diag([cosa, cosa, cosa])
    R += np.outer(direction, direction) * (1.0 - cosa)
    direction *= sina
    R += np.array([[ 0.0,         -direction[2],  direction[1]],
                      [ direction[2], 0.0,          -direction[0]],
                      [-direction[1], direction[0],  0.0]])
    M = np.identity(4)
    M[:3, :3] = R
    return (M)


def changeOrientation(mat, orientation=0, rotAxis='y', offset=[0,0,0]):
    """
    Transform orientation of bone matrix to fit the chosen coordinate system
    and mesh orientation.

    orientation: What axis points up along the model, and which direction
                     the model is facing.
        allowed values: yUpFaceZ (0), yUpFaceX (1), zUpFaceNegY (2), zUpFaceX (3)

    rotAxis: How to orient the local axes around the bone, which axis
                   points along the length of the bone. Global (g) assumes the
                   same axes as the global coordinate space used for the model.
        allowed values: y, x, g (all values)
    """
    mat = mat.copy()
    mat[:3,3] += offset

    if isinstance(orientation, str):
        oris = [ 'yUpFaceZ', 'yUpFaceX', 'zUpFaceNegY',  'zUpFaceX' ]
        try:
            orientation = oris.index(orientation)
        except:
            return None

    if orientation == 0:
        rot = np.identity(4, dtype=np.float32)
    elif orientation == 1:
        rot =_rotMatrix(math.pi/2, (0,1,0)) # rotation in y
    elif orientation == 2:
        rot = rotMatrix(math.pi/2, (1,0,0)) # rotation in X
    elif orientation == 3:
        rot =_np.dot(rotMatrix(math.pi/2, (0,0,1)), rotMatrix(math.pi/2, (1,0,0))) # dot product of Z x X

    if rotAxis.lower() == 'y':
        # Y along self, X bend
        return np.dot(rot, mat)

    elif rotAxis.lower() == 'x':
        # X along self, Y bend
        rotxy = np.dot(rotMatrix(-math.pi/2, (1,0,0)), rotMatrix(math.pi/2, (0,1,0)))
        return np.dot(rot, np.dot(mat, rotxy) )

    # Global coordinate system
    tmat = np.identity(4, float)
    tmat[:,3] = np.dot(rot, mat[:,3])
    return tmat


