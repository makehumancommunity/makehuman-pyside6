import bpy
import os

class MH2B_OT_Material:
    def __init__(self, dirname):
        self.dirname = dirname


    def addTextureNode(self, path, x, y, noncolor):
        node = self.nodes.new('ShaderNodeTexImage')
        img = os.path.join(self.dirname, path)
        node.image = bpy.data.images.load(img)
        node.location = x,y
        if noncolor:
            node.image.colorspace_settings.name = 'Non-Color'
        return (node)

    def addTexture(self, jdata, mat, texture, alpha, normtexture):
        if "source" in texture:
            img = texture["source"]
            path = jdata["images"][img]["uri"]
            print (path)

            # Add the Principled Shader node
            node_principled = self.nodes.new(type='ShaderNodeBsdfPrincipled')
            node_principled.location = 0,0

            # Add the Image Texture node
            node_tex = self.addTextureNode(path, -400, 0, False)

            # Add the Output node
            node_output = self.nodes.new(type='ShaderNodeOutputMaterial')
            node_output.location = 400,0

            # Link all nodes
            links = mat.node_tree.links
            links.new(node_tex.outputs["Color"], node_principled.inputs["Base Color"])
            links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
            if alpha is not None:
                links.new(node_tex.outputs["Alpha"], node_principled.inputs["Alpha"])

            if normtexture is not None:
                # Add the Image Texture node
                img = normtexture["source"]
                path = jdata["images"][img]["uri"]
                node_normtex = self.addTextureNode(path, -600, -400, True)

                node_normalmap = self.nodes.new('ShaderNodeNormalMap')
                node_normalmap.location = -300,-400
                links.new(node_normtex.outputs["Color"], node_normalmap.inputs["Color"])
                links.new(node_normalmap.outputs["Normal"], node_principled.inputs["Normal"])


    def addMaterial(self, jdata, material):
        matj = jdata["materials"][material]
        name = matj["name"] if "name" in matj else 'Material'
        alpha = matj["alphaMode"] if "alphaMode" in matj else None
            
        blendmat = bpy.data.materials.new(name=name)
        blendmat.use_nodes = True
        if alpha:
            blendmat.blend_method = 'BLEND'
        self.nodes = blendmat.node_tree.nodes
        self.nodes.clear()

        normtexture = None
        if "normalTexture" in matj:
            textind = matj['normalTexture']["index"]
            normtexture = jdata["textures"][textind]

        if "pbrMetallicRoughness" in matj:
            pbr = matj["pbrMetallicRoughness"]
            if 'baseColorTexture' in pbr:
                textind = pbr['baseColorTexture']["index"]
                texture = jdata["textures"][textind]
                self.addTexture(jdata, blendmat, texture, alpha, normtexture)
        return(blendmat)

