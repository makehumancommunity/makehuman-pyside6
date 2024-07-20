import bpy
import os

class MH2B_OT_Material:
    def __init__(self, dirname):
        self.dirname = dirname

    def addTexture(self, jdata, mat, texture, alpha):
        if "source" in texture:
            img = texture["source"]
            path = jdata["images"][img]["uri"]
            print (path)

            # Get the nodes
            nodes = mat.node_tree.nodes
            nodes.clear()

            # Add the Principled Shader node
            node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            node_principled.location = 0,0

            # Add the Image Texture node
            node_tex = nodes.new('ShaderNodeTexImage')
            # Assign the image
            img = os.path.join(self.dirname, path)
            node_tex.image = bpy.data.images.load(img)
            node_tex.location = -400,0

            # Add the Output node
            node_output = nodes.new(type='ShaderNodeOutputMaterial')
            node_output.location = 400,0

            # Link all nodes
            links = mat.node_tree.links
            link = links.new(node_tex.outputs["Color"], node_principled.inputs["Base Color"])
            link = links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
            if alpha is not None:
                link = links.new(node_tex.outputs["Alpha"], node_principled.inputs["Alpha"])


    def addMaterial(self, jdata, material):
        matj = jdata["materials"][material]
        name = matj["name"] if "name" in matj else 'Material'
        alpha = matj["alphaMode"] if "alphaMode" in matj else None
            
        blendmat = bpy.data.materials.new(name=name)
        blendmat.use_nodes = True
        if alpha:
            blendmat.blend_method = 'BLEND'

        if "pbrMetallicRoughness" in matj:
            pbr = matj["pbrMetallicRoughness"]
            if 'baseColorTexture' in pbr:
                textind = pbr['baseColorTexture']["index"]
                texture = jdata["textures"][textind]
                self.addTexture(jdata, blendmat, texture, alpha)
        return(blendmat)

