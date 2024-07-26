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
from bpy.props import BoolProperty


from .panel import MH2B_PT_Panel
from .load import MH2B_OT_Load


MH2B_CLASSES = [
    MH2B_OT_Load,
    MH2B_PT_Panel
]


def register():
    bpy.types.Scene.MH2B_subdiv = BoolProperty(name="Subdivision",
            description="After loading a subdivision surface modifier will be added.", default=False)
    for cls in MH2B_CLASSES:
        register_class(cls)

def unregister():
    for cls in reversed(MH2B_CLASSES):
        unregister_class(cls)

if __name__ == "__main__":
    register()
    print("module loaded")


