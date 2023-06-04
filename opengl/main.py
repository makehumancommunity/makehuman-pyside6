import OpenGL
#import OpenGL.GL as gl

def GLVersion(pinfo):
    glversion = {}
    glversion["version"] = OpenGL.__version__

    # print (gl.glGetString(gl.GL_VERSION)) TODO, add context etc.
    #
    # no shaders support will be outside this file
    #
    # without a context all other OpenGL parameter will not appear
    #
    return(glversion)
