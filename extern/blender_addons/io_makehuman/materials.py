import bpy
import os

class MH2B_OT_Material:
    def __init__(self, dirname):
        self.dirname = dirname
        self.blendmat = None
        self.nodes = None

    def addTextureNode(self, path, x, y, noncolor):
        node = self.nodes.new('ShaderNodeTexImage')
        img = os.path.join(self.dirname, path)
        node.image = bpy.data.images.load(img)
        node.location = x,y
        if noncolor:
            node.image.colorspace_settings.name = 'Non-Color'
        return (node)

    def addNodes(self, jdata, texture, alpha, roughness, normtexture):

        # Add the Principled Shader node
        #
        links = self.blendmat.node_tree.links

        node_principled = self.nodes.new(type='ShaderNodeBsdfPrincipled')
        node_principled.location = 0,0

        # Add the Output node, and link to principled
        #
        node_output = self.nodes.new(type='ShaderNodeOutputMaterial')
        node_output.location = 400,0

        links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])

        # add color, either texture or list
        #
        if isinstance(texture, dict) and "source" in texture:
            img = texture["source"]
            path = jdata["images"][img]["uri"]

            # Add the Image Texture node
            node_tex = self.addTextureNode(path, -400, 0, False)

            links.new(node_tex.outputs["Color"], node_principled.inputs["Base Color"])
            if alpha is not None:
                links.new(node_tex.outputs["Alpha"], node_principled.inputs["Alpha"])
        elif isinstance(texture, list):
            node_principled.inputs["Base Color"].default_value = tuple(texture)

        if roughness is not None:
             node_principled.inputs["Roughness"].default_value = roughness

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
            
        self.blendmat = bpy.data.materials.new(name=name)
        self.blendmat.use_nodes = True
        if alpha:
            self.blendmat.blend_method = 'BLEND'
        self.nodes = self.blendmat.node_tree.nodes
        self.nodes.clear()

        normtexture = None
        if "normalTexture" in matj:
            textind = matj['normalTexture']["index"]
            normtexture = jdata["textures"][textind]

        if "pbrMetallicRoughness" in matj:
            pbr = matj["pbrMetallicRoughness"]
            roughness = pbr['roughnessFactor'] if "roughnessFactor" in pbr else None
            if 'baseColorTexture' in pbr:
                textind = pbr['baseColorTexture']["index"]
                texture = jdata["textures"][textind]
                self.addNodes(jdata, texture, alpha, roughness, normtexture)
            elif 'baseColorFactor' in pbr:
                self.addNodes(jdata,  pbr['baseColorFactor'], alpha, roughness, normtexture)
        return(self.blendmat)

