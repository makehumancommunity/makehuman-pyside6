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
        scn = context.scene
        layout = self.layout
        fileBox = layout.box()
        fileBox.label(text="Load", icon="ARMATURE_DATA")
        fileBox.operator("mh2b.load", text="MakeHuman2 Import")
        fileBox.prop(scn, 'MH2B_subdiv', text="subdivision surface modifier")

        texbox = layout.box()
        texbox.label(text="Textures", icon="TEXTURE")
        texbox.operator("mh2b.assignprojdir", text="Assign project")
        texbox.label(text = scn.MH2B_projdir)
        texbox.prop(scn, 'MH2B_copylocal', text="Copy textures to local folder")
        texbox.label(text="Local texture folder:")
        texbox.prop(scn, 'MH2B_localtexfolder', text="")

        combox = layout.box()
        combox.label(text="Communicator", icon="USER")
        col = combox.column()
        row = col.row()
        row.label(text="Host:")
        row.prop(scn, 'MH2B_apihost', text="")

        row = col.row()
        row.label(text="Port:")
        row.prop(scn, 'MH2B_apiport', text="")

        combox.operator("mh2b.hello", text="Test connection")
        combox.operator("mh2b.getchar", text="Get character")


        combox.prop(scn, 'MH2B_feetonground', text="Place feet on ground")
        combox.prop(scn, 'MH2B_gethiddenverts', text="Get invisible vertices")
        combox.prop(scn, 'MH2B_getanimation', text="Get attached animation")
        combox.label(text="Scale:")
        combox.prop(scn, 'MH2B_getscale')

        addbox = layout.box()
        addbox.label(text="Additional functions")
        addbox.operator("mh2b.randomize", text="Randomize")

