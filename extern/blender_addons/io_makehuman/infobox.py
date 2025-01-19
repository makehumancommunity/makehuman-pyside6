#!/usr/bin/python
# -*- coding: utf-8 -*-

import bpy

class MH2B_OT_InfoBox(bpy.types.Operator):
    bl_idname = "mh2b.infobox"
    bl_label = ""

    info: bpy.props.StringProperty( name = "info", description = "information", default = '')
    error: bpy.props.StringProperty( name = "error", description = "error", default = '')
    title: bpy.props.StringProperty( name = "title", description = "title", default = '')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        box = self.layout.box()
        box.label(text=self.title)

        for line in self.info.split("\n"):
            icon = "BLANK1"
            if len(line) < 1:
                box.separator()
            else:
                if line[0] == '\001':
                    icon="CHECKBOX_HLT"
                    line=line[1:]
                elif line[0] == '\002':
                    icon="ERROR"
                    line=line[1:]
                elif line[0] == '\003':
                    icon="QUESTION"
                    line=line[1:]
                box.label(icon=icon, text=line)
        if self.error != "":
            ibox = box.box()
            ibox.alert = True
            ibox.label(icon="ERROR")
            for line in self.error.split("\n"):
                ibox.label(text=line)
        else:
            ibox = box.box()
            ibox.label(icon="CHECKBOX_HLT", text="no errors")

class MH2B_OT_WarningBox(bpy.types.Operator):
    bl_idname = "mh2b.warningbox"
    bl_label = ""

    info: bpy.props.StringProperty( name = "info", description = "information", default = '')
    title: bpy.props.StringProperty( name = "title", description = "title", default = '')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        box = self.layout.box()
        box.label(text=self.info)
        box.label(icon="ERROR", text=self.title)
