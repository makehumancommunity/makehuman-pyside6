import math
import numpy as np

"""
quaternion_matrix = quaternionToRotMatrix (3x3) ?
quaternion_from_matrix
quaternion_slerp
quaternion_multiply
"""

_EPS = np.finfo(float).eps * 4.0

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


def quaternionFromMatrix(matrix):
    """
    Return quaternion from rotation matrix.
    """
    M = np.array(matrix, dtype=np.float64, copy=False)[:4, :4]
    q = np.empty((4, ))
    t = np.trace(M)
    if t > M[3, 3]:
        q[0] = t
        q[3] = M[1, 0] - M[0, 1]
        q[2] = M[0, 2] - M[2, 0]
        q[1] = M[2, 1] - M[1, 2]
    else:
        i, j, k = 1, 2, 3
        if M[1, 1] > M[0, 0]:
            i, j, k = 2, 3, 1
        if M[2, 2] > M[i, i]:
            i, j, k = 3, 1, 2
        t = M[i, i] - (M[j, j] + M[k, k]) + M[3, 3]
        q[i] = t
        q[j] = M[i, j] + M[j, i]
        q[k] = M[k, i] + M[i, k]
        q[3] = M[k, j] - M[j, k]
    q *= 0.5 / math.sqrt(t * M[3, 3])
    if q[0] < 0.0:
        np.negative(q, q)
    return q


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


def quaternionLerp(quat0, quat1, fraction, shortestpath=True):
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


def quaternionLerpFromMatrix(mat, fraction, shortestpath=True):
    """
    do a slerp from Restmatix
    """
    m = np.identity(4, dtype=np.float32)
    m[:3, :3] = mat
    quat0 = np.asarray([1,0,0,0], dtype=np.float32)
    quat1 = quaternionFromMatrix(m)
    return (quaternionLerp(quat0, quat1, fraction, shortestpath))