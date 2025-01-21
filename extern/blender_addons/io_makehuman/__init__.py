#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Author: black-punkduck

bl_info = {
    "name": "MakeHuman2-IO",
    "author": "black-punkduck",
    "version": (0,0,1),
    "blender": (3,0,0),
    "location": "View3D > Properties > MakeHuman2-IO",
    "description": "MakeHuman2 communication.",
    "category": "MakeHuman"}

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import BoolProperty, StringProperty, IntProperty


from .panel import MH2B_PT_Panel
from .load import MH2B_OT_Load
from .api import MH2B_OT_Hello, MH2B_OT_GetChar
from .infobox import MH2B_OT_InfoBox,MH2B_OT_WarningBox

MH2B_CLASSES = [
    MH2B_OT_Load,
    MH2B_PT_Panel,
    MH2B_OT_InfoBox,
    MH2B_OT_WarningBox,
    MH2B_OT_Hello,
    MH2B_OT_GetChar
]


def register():
    scn = bpy.types.Scene
    scn.MH2B_subdiv = BoolProperty(name="Subdivision",
            description="After loading a subdivision surface modifier will be added.", default=False)
    scn.MH2B_apihost = StringProperty(name="API hostname", description="Makehuman server hostname", default="127.0.0.1")
    scn.MH2B_apiport = IntProperty(name="API Port", description="Socket port number", default=12345, min=1024, max=49151)

    for cls in MH2B_CLASSES:
        register_class(cls)

def unregister():
    for cls in reversed(MH2B_CLASSES):
        unregister_class(cls)

if __name__ == "__main__":
    register()
    print("module loaded")


