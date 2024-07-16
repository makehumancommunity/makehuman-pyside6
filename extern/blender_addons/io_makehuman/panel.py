#!/usr/bin/python
# -*- coding: utf-8 -*-

import bpy
from . import bl_info   # to get information about version

class MH2B_PT_Panel(bpy.types.Panel):
    bl_label = bl_info["name"] + " v %d.%d.%d" % bl_info["version"]
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MakeHuman 2"

    def draw(self, context):
        layout = self.layout
        fileBox = layout.box()
        fileBox.label(text="Load", icon="ARMATURE_DATA")
        fileBox.operator("mh2b.load", text="MakeHuman2 Import")


